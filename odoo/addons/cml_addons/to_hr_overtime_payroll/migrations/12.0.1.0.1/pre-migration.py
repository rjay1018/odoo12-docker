# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    # move column overtime_request_id from hr_overtime_line_single to hr_overtime_line
    cr.execute("""
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name='hr_overtime_line' and column_name='overtime_request_id';
    """)
    if not cr.fetchone():
        cr.execute("""
        ALTER TABLE hr_overtime_line ADD COLUMN overtime_request_id integer;        
        """)
    cr.execute("""
    UPDATE hr_overtime_line AS l
    SET overtime_request_id = ls.overtime_request_id
    FROM hr_overtime_line_single AS ls
        WHERE ls.line_id = l.id;
    """)

#     env = api.Environment(cr, SUPERUSER_ID, {})
#     ir_cron_scheduler_sync_attendance = env.ref('to_attendance_device.ir_cron_scheduler_sync_attendance', raise_if_not_found=False)
#     if ir_cron_scheduler_sync_attendance:
#         ir_cron_scheduler_sync_attendance.write({
#             'function': 'cron_sync_attendance'
#             })
