from odoo import http, _
from odoo.http import request
from datetime import datetime, date


class Appointment(http.Controller):


	@http.route('/web/appointment/filter', type='json', auth="public")
	def get_appointment_availibility(self, support_id, counselor_id, slot_id, s_date):
		today_date = date.today()
		s_date = str(s_date)
		year,month,day = (int(x) for x in s_date.split('-'))
		weekday = str(date(year,month,day).weekday())
		appointment_available = False
		if not date(year,month,day) >= today_date:
			return False

		support_employee = []
		counselor_employee = []
		slot_employee = []
		emp_domain = [('is_specialist','=',True)]
		employee_ids = False
# 		if support_id or counselor_id or slot_id:
		employee_ids = request.env['hr.employee'].sudo().search(emp_domain)

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
		

	@http.route('/new/appointment', type='http', auth='public', website=True)
	def appointment(self, **kw):
		slot_ids = request.env['specialist.availability'].sudo().search([])
		support_ids = request.env['client.support'].sudo().search([])
		counselor_ids = request.env['hr.employee'].sudo().search([('is_specialist','=',True)])

		return http.request.render('ki_appointment_management.appointment_template',{
			'slot_ids' : slot_ids,
			'support_ids' : support_ids,
			'counselor_ids' : counselor_ids
		})


	@http.route(['/new/appointment/create/<int:day>'], type='http', auth='user', website=True)
	def appointment_create(self,day, **kw):
		date = kw.get('date')
		datetime_str = str(date)
		datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')
		employee_ids = request.env['hr.employee'].sudo().search([('is_specialist','=',True)])
		availability_id = request.env['specialist.availability'].sudo().search([])
		product_ids = request.env['product.product'].sudo().search([('type','=','service')])
		default_product_id = False
		if kw.get('sd'):
			try:
				new_id = int(kw.get('sd'))
				support_id = request.env['client.support'].sudo().search([('id','=',new_id)])
				default_product_id = support_id.product_id.id if support_id.product_id else False
				employee_ids = employee_ids.filtered(lambda l: support_id.id in l.client_support_ids.ids)
			except:
				default_product_id = False
				pass
		try:
			new_emp_id = int(kw.get('ed'))
			if new_emp_id:
				employee_ids = employee_ids.filtered(lambda l:l.id == new_emp_id)
		except:
			pass
		vals = {
			'current_date' : kw.get('date'),
			'hr_employee_ids' : employee_ids,
			'availability_ids' : availability_id,
			'week' : str(datetime_object.weekday()),
			'product_ids': product_ids,
			'default_product_id' : default_product_id,
			'default_name' : request.env.user.name
		}
		return http.request.render('ki_appointment_management.appointment_create',vals)

	@http.route(['/new/appointment/submit/'], type='http', auth='user', website=True)
	def appointment_submit(self, **kw):
		if not kw.get('slot_id'):
			date = kw.get('date')
			datetime_str = str(date)
			datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d')
			employee_ids = request.env['hr.employee'].sudo().search([('is_specialist', '=', True)])
			availability_id = request.env['specialist.availability'].sudo().search([])
			product_ids = request.env['product.product'].sudo().search([('type', '=', 'service')])
			ss = kw.get('hr_employee_ids')
			if ss:
				new_empl = ss.split(',')
			employee_ids = employee_ids.filtered(lambda l:str(l.id) in new_empl)
			vals = {
				'current_date': kw.get('date'),
				'hr_employee_ids': employee_ids,
				'availability_ids': availability_id,
				'week': str(datetime_object.weekday()),
				'product_ids': product_ids,
				'error' : "No Slot Selected !!.",
				'default_name': request.env.user.name
			}
			return http.request.render('ki_appointment_management.appointment_create', vals)
		id_list = kw.get('slot_id').split(',')
		employee_id = int(id_list[0])
		slot_id = int(id_list[1])
		date = kw.get('date')
		name = kw.get('name')
		#description = kw.get('description')
		product_id = kw.get('service_id')
		availability_id = request.env['specialist.availability'].sudo().search([('id', '=', int(slot_id))])

		if date:
			datetime_str = str(date) + " %02d:%02d:%s" % (int(availability_id.time), availability_id.time % 1 * 60,'00')
			datetime_object = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
			request.env['clinic.appointment'].sudo().create({
				'employee_id': employee_id,
				'name': name,
				#'notes': description,
				'product_id' : product_id,
				'session_start': datetime_object,
				'partner_id': request.env.user.partner_id.id
			})
			request.env['hr.employee.slots'].sudo().create({
				'employee_id' : employee_id,
				'slot_id' : slot_id,
				'date' : date
			})
		return request.redirect("/new/appointment")
