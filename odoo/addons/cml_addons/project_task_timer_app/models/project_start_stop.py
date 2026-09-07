# -*- coding: utf-8 -*-

from itertools import groupby
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp


class Inherit_project_task(models.Model):
	_inherit = 'account.analytic.line'

	def start_stop_fast_timesheet(self,count):
		if count == 1:
			return False
		else:
			return True

	def start_fast_timesheet(self , count):
		if count == 1:
			return True
		else:
			return False


class Inherit_project_task(models.Model):
	_inherit = 'project.task'

	time_count = fields.Float("Time")
	is_user_working = fields.Boolean("Is User Working")
	task_run = fields.Boolean("Task Run")
	task_pause = fields.Boolean("Task Pause",default=False)
	duration_ids = fields.One2many(
		'project.calculate.duration','production_id',string="Duraction")
	is_started = fields.Boolean("Started" ,default=False)
	chack_if_play = fields.Boolean("Check Play",default=False)

	@api.one
	@api.depends('duration_ids.duration')
	def _compute_duration(self):
		self.time_count = sum(self.duration_ids.mapped('duration'))

	@api.multi
	def run_task(self):	

		all_task = self.env['project.task'].search([('chack_if_play','=',True),('project_id','=',self.project_id.id)])
		if all_task :
			return {
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'task.start.wiz',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'res_id': False,
				'name' : 'You have certain running task'
			}
		else:
			self.start_play()

	@api.multi
	def start_play(self):
		self.is_started == True
		self.is_user_working = True
		self.task_run = True
		self.task_pause = False
		self.is_started = True
		self.chack_if_play = True
		self.ensure_one()
		timeline = self.env['project.calculate.duration']

		for taskes in self:
			timeline.create({
				'production_id': taskes.id,
				'date_start': datetime.now(),
				'user_id': self.env.user.id
			})

	@api.multi
	def unpause_task(self):
		self.is_user_working = True
		self.task_pause = False
		self.is_started = True
		self.chack_if_play = True
		self.ensure_one()
		timeline = self.env['project.calculate.duration']

		for taskes in self:
			timeline.create({
				'production_id': taskes.id,
				'date_start': datetime.now(),
				'user_id': self.env.user.id
			})

	@api.multi
	def pause_task(self):
		self.is_user_working = False
		self.task_pause = True
		self.is_started = True	
		self.chack_if_play = False
		self.end_previous()
		return True
		
	@api.multi
	def stop_task(self):
		self.end_previous()
		return {
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'wiz.stop.task',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'res_id': False,
				'name': 'Description',
			}

	@api.multi
	def end_previous(self, doall=False):
		calculate_obj = self.env['project.calculate.duration']
		domain = [('production_id', 'in', self.ids), ('date_end', '=', False)]
		if not doall:
			domain.append(('user_id', '=', self.env.user.id))

		not_calculate_timelines = calculate_obj.browse()
		for dur in calculate_obj.search(domain, limit=None if doall else 1):
			wo = dur.production_id
			not_calculate_timelines += dur
			dur.write({'date_end': fields.Datetime.now()})
		return True

class project_duration_calculation(models.Model):
	_name = "project.calculate.duration"
	production_id = fields.Many2one('project.task', string='Manufacturing Order', readonly='True')
	user_id = fields.Many2one(
		'res.users', "User",
		default=lambda self: self.env.uid)
	date_start = fields.Datetime('Start Date', default=fields.Datetime.now, required=True)
	date_end = fields.Datetime('End Date')
	duration = fields.Float('Duration', compute='_compute_duration', store=True)

	@api.depends('date_end', 'date_start')
	def _compute_duration(self):
		for blocktime in self:
			if blocktime.date_end:
				d1 = fields.Datetime.from_string(blocktime.date_start)
				d2 = fields.Datetime.from_string(blocktime.date_end)
				diff = d2 - d1
				blocktime.duration = round(diff.total_seconds() / 60.0, 2) + 0.01
			else:
				blocktime.duration = 0.0

class wizard_stop_task(models.TransientModel):
	_name = "wiz.stop.task"
	description = fields.Char("Description",required=True)

	@api.multi
	def submit_desc(self):
		active_model_id = self.env['project.task']._context.get('active_id')
		task_project = self.env['project.task'].browse(active_model_id)
		task_project.is_user_working = False
		task_project.task_run = False

		total_duration = 0.0
		for pro_task in task_project:
			for lines in pro_task.duration_ids:
				total_duration += lines.duration/60
		employee = self.env['hr.employee'].search([('name','=',task_project.user_id.name)])	

		task_project.timesheet_ids.create({
			'date' : fields.date.today(),
			'name' : self.description,
			'task_id' : task_project.id,
			'project_id' : task_project.project_id.id,
			'unit_amount': total_duration,		
			})

		task_project.duration_ids.unlink()
		task_project.is_started = False
		task_project.chack_if_play = False

		return True

class wizard_stop_task(models.TransientModel):
	_name = "task.start.wiz"

	@api.multi
	def sub_start(self):
		tasks = self.env['project.task']._context.get('active_id')
		bro_task = self.env['project.task'].browse(tasks)
		count = 0
		all_task_id = self.env['project.task'].search([('chack_if_play','=',True),('project_id','=',bro_task.project_id.id)])

		for i in all_task_id:
			i.is_user_working = False
			i.task_pause = True
			i.is_started = True	
			i.chack_if_play = False
			i.end_previous()
			count = 1

		if count == 1:
			bro_task.start_play()

		return {
				'type': 'ir.actions.client',
				'tag': 'reload',
				}
