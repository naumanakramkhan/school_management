# -*- coding: utf-8 -*-
"""Move existing school.student rows into res.partner (Contacts).

Runs before the module code is loaded. Steps:
  1. add the new student columns to res_partner
  2. create (or reuse, matched by email + name) a Contact per old student
  3. remap student ids in attendance, grades, course enrolment, xml ids, chatter
  4. keep the old table as school_student_backup
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("SELECT to_regclass('school_student')")
    if not cr.fetchone()[0]:
        return

    env = api.Environment(cr, SUPERUSER_ID, {'tracking_disable': True, 'mail_create_nolog': True})
    Partner = env['res.partner']

    # 1. new columns on res_partner
    cr.execute("""
        ALTER TABLE res_partner
            ADD COLUMN IF NOT EXISTS is_student boolean,
            ADD COLUMN IF NOT EXISTS student_code varchar,
            ADD COLUMN IF NOT EXISTS student_dob date,
            ADD COLUMN IF NOT EXISTS student_gender varchar
    """)

    # 2. contact per student
    cr.execute("""SELECT id, name, student_id, gender, email, phone, date_of_birth, address, active
                  FROM school_student ORDER BY id""")
    mapping = {}
    for old_id, name, code, gender, email, phone, dob, address, active in cr.fetchall():
        partner_id = False
        if email:
            cr.execute("""SELECT id FROM res_partner
                          WHERE lower(email) = lower(%s) AND lower(name) = lower(%s)
                          ORDER BY id LIMIT 1""", (email, name))
            row = cr.fetchone()
            partner_id = row and row[0]
        if not partner_id:
            partner_id = Partner.create({
                'name': name, 'email': email, 'phone': phone,
                'street': address, 'active': active,
            }).id
        cr.execute("""UPDATE res_partner
                      SET is_student = true, student_code = %s, student_dob = %s, student_gender = %s
                      WHERE id = %s""", (code, dob, gender, partner_id))
        mapping[old_id] = partner_id

    if not mapping:
        return
    _logger.info("school_management: moved %s students into res.partner", len(mapping))

    # 3. remap references (single UPDATE ... FROM so overlapping ids cannot collide)
    cr.execute("CREATE TEMP TABLE _student_map (old_id int PRIMARY KEY, new_id int) ON COMMIT DROP")
    cr.executemany("INSERT INTO _student_map VALUES (%s, %s)", list(mapping.items()))

    # drop old foreign keys that point at school_student
    cr.execute("""SELECT conrelid::regclass::text, conname FROM pg_constraint
                  WHERE contype = 'f' AND confrelid = 'school_student'::regclass""")
    for table, conname in cr.fetchall():
        cr.execute('ALTER TABLE %s DROP CONSTRAINT "%s"' % (table, conname))

    for table, col in (('school_attendance', 'student_id'),
                       ('school_grade', 'student_id'),
                       ('school_course_school_student_rel', 'school_student_id')):
        cr.execute("SELECT to_regclass(%s)", (table,))
        if cr.fetchone()[0]:
            cr.execute("UPDATE %s t SET %s = m.new_id FROM _student_map m WHERE t.%s = m.old_id"
                       % (table, col, col))

    # demo / data xml ids now point to the contacts
    cr.execute("""UPDATE ir_model_data d SET model = 'res.partner', res_id = m.new_id
                  FROM _student_map m
                  WHERE d.module = 'school_management' AND d.model = 'school.student'
                    AND d.res_id = m.old_id""")
    # chatter history
    cr.execute("""UPDATE mail_message msg SET model = 'res.partner', res_id = m.new_id
                  FROM _student_map m
                  WHERE msg.model = 'school.student' AND msg.res_id = m.old_id""")

    # 4. keep a backup of the old table
    cr.execute("DROP TABLE IF EXISTS school_student_backup")
    cr.execute("ALTER TABLE school_student RENAME TO school_student_backup")
