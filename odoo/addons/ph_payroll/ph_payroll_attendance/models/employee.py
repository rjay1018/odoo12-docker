from odoo import models, api


class Employee(models.Model):
    _inherit = "hr.employee"

    @api.multi
    def attendance_action(self, next_action):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        # Added kiosk in context to trigger computation

        self.ensure_one()
        action_message = self.env.ref('hr_attendance.hr_attendance_action_greeting_message').read()[0]
        action_message['previous_attendance_change_date'] = self.last_attendance_id and (self.last_attendance_id.check_out or self.last_attendance_id.check_in) or False
        action_message['employee_name'] = self.name
        action_message['barcode'] = self.barcode
        action_message['next_action'] = next_action

        if self.user_id:
            modified_attendance = self.sudo(self.user_id.id).with_context(kiosk=True).attendance_action_change()
        else:
            modified_attendance = self.sudo().with_context(kiosk=True).attendance_action_change()

        action_message['attendance'] = modified_attendance.read()[0]
        return {'action': action_message}