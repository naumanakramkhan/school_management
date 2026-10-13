# -*- coding: utf-8 -*-
"""Move existing school.teacher rows into res.partner (Contacts)."""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("SELECT to_regclass('school_teacher')")
    if not cr.fetchone()[0]:
        return

    env = api.Environment(cr, SUPERUSER_ID, {'tracking_disable': True, 'mail_create_nolog': True})
    Partner = env['res.partner']

    cr.execute("""
        ALTER TABLE res_partner
            ADD COLUMN IF NOT EXISTS is_teacher boolean,
            ADD COLUMN IF NOT EXISTS teacher_code varchar,
            ADD COLUMN IF NOT EXISTS teacher_subject varchar,
            ADD COLUMN IF NOT EXISTS teacher_qualification varchar,
            ADD COLUMN IF NOT EXISTS teacher_joining_date date,
            ADD COLUMN IF NOT EXISTS teacher_experience_years integer
    """)

    cr.execute("""SELECT id, name, teacher_id, subject, email, phone, address,
                         date_of_joining, qualification, experience_years, active
                  FROM school_teacher ORDER BY id""")
    mapping = {}
    for (old_id, name, code, subject, email, phone, address,
         joining, qualification, experience, active) in cr.fetchall():
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
                      SET is_teacher = true, teacher_code = %s, teacher_subject = %s,
                          teacher_qualification = %s, teacher_joining_date = %s,
                          teacher_experience_years = %s
                      WHERE id = %s""",
                   (code, subject, qualification, joining, experience, partner_id))
        mapping[old_id] = partner_id

    if not mapping:
        return
    _logger.info("school_management: moved %s teachers into res.partner", len(mapping))

    cr.execute("CREATE TEMP TABLE _teacher_map (old_id int PRIMARY KEY, new_id int) ON COMMIT DROP")
    cr.executemany("INSERT INTO _teacher_map VALUES (%s, %s)", list(mapping.items()))

    cr.execute("""SELECT conrelid::regclass::text, conname FROM pg_constraint
                  WHERE contype = 'f' AND confrelid = 'school_teacher'::regclass""")
    for table, conname in cr.fetchall():
        cr.execute('ALTER TABLE %s DROP CONSTRAINT "%s"' % (table, conname))

    for table in ('school_course', 'school_grade'):
        cr.execute("SELECT to_regclass(%s)", (table,))
        if cr.fetchone()[0]:
            cr.execute("UPDATE %s t SET teacher_id = m.new_id FROM _teacher_map m "
                       "WHERE t.teacher_id = m.old_id" % table)

    cr.execute("""UPDATE ir_model_data d SET model = 'res.partner', res_id = m.new_id
                  FROM _teacher_map m
                  WHERE d.module = 'school_management' AND d.model = 'school.teacher'
                    AND d.res_id = m.old_id""")
    cr.execute("""UPDATE mail_message msg SET model = 'res.partner', res_id = m.new_id
                  FROM _teacher_map m
                  WHERE msg.model = 'school.teacher' AND msg.res_id = m.old_id""")

    cr.execute("DROP TABLE IF EXISTS school_teacher_backup")
    cr.execute("ALTER TABLE school_teacher RENAME TO school_teacher_backup")
