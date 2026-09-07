# -*- coding: utf-8 -*-

from odoo import models, fields, api,exceptions,_
from odoo.tools import float_compare
from datetime import *

import datetime

class HrEmployee(models.Model):
	_inherit='hr.employee'

	hr_slots_ids = fields.One2many(
		'hr.employee.slots',
		'employee_id',
		string = "Appointment Slots"
	)

	client_support_ids = fields.Many2many(
		'client.support',
		string="Client Supports"
	)

	@api.model
	def get_appointment_availibility(self,support_id,counselor_id,slot_id,s_date):
		today_date = datetime.date.today()
		s_date = str(s_date)
		year,month,day = (int(x) for x in s_date.split('-'))
		weekday = str(datetime.date(year,month,day).weekday())
		appointment_available = False
		if not datetime.date(year,month,day) >= today_date:
			return False

		support_employee = []
		counselor_employee = []
		slot_employee = []
		emp_domain = [('is_specialist','=',True)]
		employee_ids = False
		if support_id or counselor_id or slot_id:
			employee_ids = self.env['hr.employee'].sudo().search(emp_domain)

		if support_id:
			for employee_ in employee_ids:
				if employee_.schedule_line_ids.filtered(lambda l : int(l.day) == int(weekday)) and employee_.client_support_ids.filtered(lambda l : int(l.id) == int(support_id)):
					support_employee.append(int(employee_.id))

			employee_ids = employee_ids.filtered(lambda l:l.id in support_employee)

		if counselor_id:
			for employee_ in employee_ids:
				if employee_.schedule_line_ids.filtered(lambda l: int(l.day) == int(weekday)) and int(employee_.id) == int(counselor_id):
					counselor_employee.append(int(employee_.id))

			employee_ids = employee_ids.filtered(lambda l : l.id in counselor_employee)

		if slot_id:
			for employee_ in employee_ids:
				if employee_.schedule_line_ids.filtered(lambda l: int(l.day) == int(weekday)) and not employee_.hr_slots_ids.filtered(lambda l:l.date == datetime.date(year,month,day) and int(l.slot_id) == int(slot_id)):
					for schedule_id in employee_.schedule_line_ids.filtered(lambda l: int(l.day) == int(weekday)):
						if schedule_id.availability_ids.filtered(lambda l: int(l.id) == int(slot_id)):
							slot_employee.append(int(employee_.id))
							break;

			employee_ids = employee_ids.filtered(lambda l:l.id in slot_employee)

		if employee_ids:
			return True
		else:
			return False

		'''
		
		print("-"*50)
		print(weekday)
		print(employee_.schedule_line_ids.filtered(lambda l : int(l.day) == int(weekday)))
		print(appointment_available)
		print("-" * 50)



		return appointment_available

		if support_id and counselor_id and slot_id:
			support = self.env['client.support'].sudo().search([('id','=',support_id)])
			counselor = self.env['hr.employee'].sudo().search([('id','=',counselor_id)])
			slot = self.env['specialist.availability'].sudo().search([('id','=',slot_id)])

			count = 0
			counselor_days = []
			for value in counselor.schedule_line_ids:
				counselor_days.append(value.day)

			if weekday in counselor_days:
				for value in counselor.client_support_ids:
					if value.id == support.id:
						count += 1
				for value1 in counselor.schedule_line_ids:
					if str(value1.day) == weekday:
						for value2 in value1.availability_ids:
							if value2.id == slot.id:
								count +=1
				if count == 2:
					return True
				else:
					return False
			else:
				return False

		elif support_id and counselor_id:
			counselor = self.env['hr.employee'].sudo().search([('id','=',counselor_id)])

			count = 0
			for value in counselor.client_support_ids:
				if value.id == int(support_id):
					count = 1

			if count == 1:
				counselor_days = []
				for value in counselor.schedule_line_ids:
					counselor_days.append(value.day)
				if weekday in counselor_days:
					return True
				else:
					return False
			else:
				return False
				
		# elif counselor_id and slot_id:
		# 	counselor = self.env['hr.employee'].sudo().search([('id','=',counselor_id)])

		# 	for value in counselor.schedule_line_ids:
		# 		print(weekday,value.day)
		# 		if str(value.day) == weekday:
		# 			for value1 in value.availability_ids:
		# 				if value1.id == int(slot_id):
		# 					return True
		# 				else:
		# 					return False
		# 		else:
		# 			return False

		elif support_id:
			counselor_ids = self.env['hr.employee'].sudo().search([('is_specialist','=',True)])
			counselors = []
			for counselor in counselor_ids:
				for value in counselor.client_support_ids:
					if value.id == int(support_id):
						counselors.append(counselor)

			counselor_days = []
			for counselor in counselors:
				for value in counselor.schedule_line_ids:
					counselor_days.append(value.day)

			if weekday in counselor_days:
				return True
			else:
				return False

		elif counselor_id:
			counselor = self.env['hr.employee'].sudo().search([('id','=',counselor_id)])

			counselor_days = []
			for value in counselor.schedule_line_ids:
				counselor_days.append(value.day)

			if weekday in counselor_days:
				return True
			else:
				return False

		else:
			return False
			
		'''