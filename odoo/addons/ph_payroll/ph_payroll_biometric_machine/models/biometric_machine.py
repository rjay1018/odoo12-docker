# -*- coding: utf-8 -*-

from odoo import models,fields,api,exceptions,SUPERUSER_ID,_
from odoo.exceptions import UserError, ValidationError

from datetime import datetime , timedelta
import pytz
import time

from . import const
from .base import ZK

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)

class zkMachineLocation(models.Model):
    _name= 'zk.machine.location'
    name = fields.Char("Location",required=True)


class zkMachine(models.Model):
    _name= 'zk.machine'
    
    name =  fields.Char("Machine IP")
    state =  fields.Selection([('draft','Draft'),('done','Done')], 'State', default='draft')
    location_id =  fields.Many2one('zk.machine.location', string="Location")
    port =  fields.Integer("Port Number")
    employee_ids = fields.Many2many("hr.employee", 'zk_machine_employee_rel', 'employee_id', 'machine_id',string='Employees', readonly=True, copy=False, required=False)
    
    @api.multi
    def try_connection(self):
        for r in self:
            machine_ip = r.name
            port = r.port
            zk = ZK(machine_ip, port=port, timeout=50, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                users = conn.get_users()
            except Exception as e:
                raise UserError('The connection has not been achieved')
            finally:
                if conn:
                    conn.disconnect()
                    raise UserError(_('Successful connection:  "%s".') %
                            (users))

    @api.multi
    def restart(self):
        for r in self:
            machine_ip = r.name
            port = r.port
            zk = ZK(machine_ip, port=port, timeout=5, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.restart()
            except Exception as e:
                raise UserError('Process terminate')
            # finally:
            #     if conn:
            #         conn.disconnect()
                    
    @api.multi
    def synchronize(self):
        for r in self:
            employee  = self.env['hr.employee']
            employee_location_line=self.env['zk.employee.location.line']
            employee_list = []
            machine_ip = r.name
            port = r.port
            zk = ZK(machine_ip, port=port, timeout=5, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            
            try:
                conn = zk.connect()
                conn.disable_device()
                users = conn.get_users()
                for user in users:
                    employee_id=employee.search([('zknumber','=',user.user_id)])
                    if employee_id:
                        employee_list.append(employee_id)
                        if employee_id not in r.employee_ids:
                            r.employee_ids += employee_id
                            employee_location_line.create({'employee_id':employee_id.id,
                                                           'zk_num':employee_id.zknumber,
                                                           'machine_id':r.id,
                                                           'uid':user.uid,
                                                           'location_id':r.location_id.id})
                for emp in employee_list:
                    employee+=emp
                employees_unlink = r.employee_ids - employee
                for emp1 in employees_unlink:
                    employee_location_line_id = employee_location_line.search([('employee_id','=',emp1.id),('machine_id','=',r.id)])
                    employee_location_line_id.unlink()
                r.employee_ids = employee
            except Exception as e:
                raise UserError('The connection has not been achieved')
            finally:
                if conn:
                    conn.disconnect()
                    
    @api.multi
    def clear_attendance(self):
        for r in self:
            machine_ip = r.name
            port = r.port
            zk = ZK(machine_ip, port=port, timeout=5, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.disable_device()
                conn.clear_attendance()
            except Exception as e:
                raise UserError('The connection has not been achieved')
            finally:
                if conn:
                    conn.enable_device()
                    conn.disconnect()
    
    @api.multi
    def download_attendance2(self):
        users  = self.env['res.users']
        attendance_obj =  self.env["hr.attendance"]
        employee_location_line_obj = self.env["zk.employee.location.line"]
        user = self.env.user
        if not user.partner_id.tz:
            raise exceptions.ValidationError("Timezone is not defined on this %s user." % user.name)
        tz = pytz.timezone(user.partner_id.tz) or False
        for machine in self:
            machine_ip = machine.name
            port = machine.port
            zk = ZK(machine_ip, port=port, timeout=50, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                attendances = conn.get_attendance()
            except Exception as e:
                print (e)
                raise UserError('The connection has not been achieved')
            finally:
                if conn:
                    conn.disconnect()
                    raise UserError(_('Successful connection:  "%s".') %
                            (attendances))

    @api.multi
    def download_attendance(self):
        users  = self.env['res.users']
        attendance_obj =  self.env["hr.attendance"]
        machine_att_obj =  self.env["zk.machine.attendance"]
        employee_location_line_obj = self.env["zk.employee.location.line"]
        user = self.env.user
        if not user.partner_id.tz:
            raise exceptions.ValidationError("Timezone is not defined on this %s user." % user.name)
        tz = pytz.timezone('Asia/Manila')
        for machine in self:
            machine_ip = machine.name
            port = machine.port
            zk = ZK(machine_ip, port=port, timeout=10, password=0, force_udp=False, ommit_ping=False)
            conn = ''
            try:
                conn = zk.connect()
                conn.disable_device()
                attendances = conn.get_attendance()
                for attendance in attendances:
                    employee_location_line = employee_location_line_obj.search([('zk_num', '=', int(attendance.user_id)), ('location_id', '=', machine.location_id.id), ('machine_id', '=', machine.id)])
                    if employee_location_line:
                        employee_id = employee_location_line.employee_id

                        date = attendance.timestamp
                        date1 = datetime.strptime(str(date), DEFAULT_SERVER_DATETIME_FORMAT)
                        date = tz.normalize(tz.localize(date1)).astimezone(pytz.utc).strftime ("%Y-%m-%d %H:%M:%S")

                        machine_att_obj.create({
                                'employee_id': employee_id.id,
                                'punch_type': str(attendance.punch),
                                'punch_time': date
                            })

            except Exception as e:
                raise UserError(e)
            finally:
                if conn:
                    conn.enable_device()
                    conn.disconnect()

    @api.model
    def cron_download_attendance(self):
        machines = self.env['zk.machine'].search([])
        for machine in machines :
            machine.download_attendance()
            

class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    
    check_in = fields.Datetime(string="Check In", default='', required=False)
    
    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_in and attendance.check_out:
                delta = attendance.check_out - attendance.check_in
                attendance.worked_hours = delta.total_seconds() / 3600.0
        
    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        pass


class hrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    zk_location_line_ids = fields.One2many('zk.employee.location.line','employee_id',string='Locations')
    zknumber =  fields.Char("ZK Number")
    
    @api.one
    def delete_employee_zk(self):
        machine_id = self.env['zk.machine'].search([('id','=',int(self.env.context.get('machine_id')))])
        machine_ip = machine_id.name
        port = machine_id.port
        zk = ZK(machine_ip, port=port, timeout=5, password=0, force_udp=False, ommit_ping=False)
        conn = ''
        try:
            conn = zk.connect()
            conn.disable_device()
            employee_location_line = self.env['zk.employee.location.line'].search([('employee_id','=',self.id),('machine_id','=',machine_id.id)])
            conn.delete_user(uid=employee_location_line.uid)
            machine_id.employee_ids = machine_id.employee_ids - self
            employee_location_line.unlink()
        except Exception as e:
            raise UserError('Unable to complete user registration')
        finally:
            if conn != '':
                conn.enable_device()
                conn.disconnect()
        return True
      
    @api.one
    def disassociate_employee_zk(self):
        machine_id = self.env['zk.machine'].search([('id','=',int(self.env.context.get('machine_id')))])
        employee_location_line = self.env['zk.employee.location.line'].search([('employee_id','=',self.id),('machine_id','=',machine_id.id)])
        machine_id.employee_ids = machine_id.employee_ids - self
        employee_location_line.unlink()
        return True


class hrZkEmployeeLocationLine(models.Model):
    _name = 'zk.employee.location.line'

    employee_id = fields.Many2one('hr.employee',string="Employee")
    zk_num = fields.Integer(string="ZKSoftware Number", help="ZK Attendance User Code",required=True)
    machine_id = fields.Many2one('zk.machine',string="Machine",required=True)
    location_id =  fields.Many2one('zk.machine.location',related='machine_id.location_id', string="Location")
    uid =  fields.Integer('Uid')
    
    _sql_constraints = [('unique_location_emp', 'unique(employee_id,location_id)', 'There is a record of this employee for this location.')]
    

class zkMachineAttendance(models.Model):
    _name = 'zk.machine.attendance'
    _rec_name = 'punch_time'
    _order = 'employee_id, punch_time'

    PUNCH_TYPE = [
        ('0', 'Check In'),
        ('1', 'Check Out'),
        ('2', 'Break Out'),
        ('3', 'Break In'),
        ('4', 'Overtime In'),
        ('5', 'Overtime Out')
    ]

    @api.model
    def create(self, vals):
        if 'zknumber' in vals and vals['zknumber']:
            emp = self.env['hr.employee'].search([('zknumber', '=', vals['zknumber'])])
            if emp:
                vals['employee_id'] = emp.id
            else:
                raise ValidationError(_('No employee found related to this ZK Number: %s' % (vals['zknumber'])))
        return super(zkMachineAttendance, self).create(vals)

    employee_id = fields.Many2one('hr.employee', string='Employee', ondelete='cascade', index=True, required=True)
    zknumber =  fields.Char('ZK Number')
    punch_type = fields.Selection(PUNCH_TYPE, string='Punching Type', required=True)
    punch_time = fields.Datetime(string='Punching Time', required=True)
    import_done = fields.Boolean()

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.zknumber = self.employee_id.zknumber

    @api.multi
    def download_attendance(self):
        machines = self.env['zk.machine'].search([])
        for machine in machines :
            machine.download_attendance()

    @api.multi
    def regular_schedule(self, employee_id):
        contract = self.env['hr.contract'].get_active_contract(employee_id, contract_obj=True)
        if contract.work_shift_fix:
            return True
        else: return False

    @api.multi
    def import_attendance(self):
        tz = pytz.timezone('Asia/Manila')
        attendance_obj =  self.env['hr.attendance']

        attendance_ids = self._context.get('active_ids')
        if not attendance_ids:
            raise UserError(_('Please select attendance to process'))

        for att_id in attendance_ids:
            att = self.browse(att_id)
            if self.regular_schedule(att.employee_id):
                ### MORNING ###
                if att.punch_type == '0':
                    attendance_id = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_in', '=', str(att.punch_time)), ('day_period', '=', 'morning')])
                    if not attendance_id:
                        attendance_obj.create({'check_in': att.punch_time, 'employee_id': att.employee_id.id, 'day_period': 'morning'})

                if att.punch_type == '2':
                    attendance_id = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_out', '=', str(att.punch_time)), ('day_period', '=', 'morning')])
                    if not attendance_id:
                        attendance_ids = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_in', '<', str(att.punch_time)), ('day_period', '=', 'morning')], order='check_in')
                        if attendance_ids:
                            found = False
                            for attendance in reversed(attendance_ids):
                                if datetime.strptime(str(attendance.check_in), '%Y-%m-%d %H:%M:%S').date() == datetime.strptime(str(att.punch_time), '%Y-%m-%d %H:%M:%S').date():
                                    attendance.write({'check_out': att.punch_time, 'day_period': 'morning'})
                                    found = True
                                    break
                                attendance_id = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_in', '=', str(att.punch_time)), ('day_period', '=', 'morning')])
                                if not attendance_id:
                                    attendance_obj.create({'check_in': att.punch_time, 'check_out': att.punch_time, 'employee_id': att.employee_id.id, 'day_period': 'morning'})
                        else:
                            attendance_obj.create({'check_out': att.punch_time, 'employee_id': att.employee_id.id, 'day_period': 'morning'})

                ### AFTERNOON ###
                if att.punch_type == '3':
                    attendance_id = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_in', '=', str(att.punch_time)), ('day_period', '=', 'afternoon')])
                    if not attendance_id:
                        attendance_obj.create({'check_in': att.punch_time, 'employee_id': att.employee_id.id, 'day_period': 'afternoon'})

                if att.punch_type == '1':
                    attendance_id = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_out', '=', str(att.punch_time)), ('day_period', '=', 'afternoon')])
                    if not attendance_id:
                        attendance_ids = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_in', '<', str(att.punch_time)), ('day_period', '=', 'afternoon')], order='check_in')
                        if attendance_ids:
                            found = False
                            for attendance in reversed(attendance_ids):
                                if datetime.strptime(str(attendance.check_in), '%Y-%m-%d %H:%M:%S').date() == datetime.strptime(str(att.punch_time), '%Y-%m-%d %H:%M:%S').date():
                                    attendance.write({'check_out': att.punch_time, 'day_period': 'afternoon'})
                                    found = True
                                    break
                                attendance_id = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_in', '=', str(att.punch_time)), ('day_period', '=', 'afternoon')])
                                if not attendance_id:
                                    attendance_obj.create({'check_in': att.punch_time, 'check_out': att.punch_time, 'employee_id': att.employee_id.id, 'day_period': 'afternoon'})
                        else:
                            attendance_obj.create({'check_out': att.punch_time, 'employee_id': att.employee_id.id, 'day_period': 'afternoon'})

            else:
                if att.punch_type == '0':
                    attendance_id = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_in', '=', str(att.punch_time))])
                    if not attendance_id:
                        attendance_obj.create({'check_in': att.punch_time, 'employee_id': att.employee_id.id})

                if att.punch_type == '1':
                    attendance_id = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_out', '=', str(att.punch_time))])
                    if not attendance_id:
                        attendance_ids = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_in', '<', str(att.punch_time))], order='check_in')
                        if attendance_ids:
                            found = False
                            for attendance in reversed(attendance_ids):
                                if datetime.strptime(str(attendance.check_in), '%Y-%m-%d %H:%M:%S').date() == datetime.strptime(str(att.punch_time), '%Y-%m-%d %H:%M:%S').date():
                                    attendance.write({'check_out': att.punch_time})
                                    found = True
                                    break
                                attendance_id = attendance_obj.search([('employee_id', '=', att.employee_id.id), ('check_in', '=', str(att.punch_time))])
                                if not attendance_id:
                                    attendance_obj.create({'check_in': att.punch_time, 'check_out': att.punch_time, 'employee_id': att.employee_id.id})
                        else:
                            attendance_obj.create({'check_out': att.punch_time, 'employee_id': att.employee_id.id})

            att.import_done = True
