from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Overtime(models.Model):
    _inherit = 'hr.overtime'

    def _get_computation(self):
        self.computation_ids = None
        comp = None
        obj_att = self.env['hr.attendance']

        local_ot_fr = obj_att._localize_dt(self.ot_fr)
        ot_fr = local_ot_fr.replace(tzinfo=None)

        local_ot_to = obj_att._localize_dt(self.ot_to)
        ot_to = local_ot_to.replace(tzinfo=None)

        ot_hrs_list = []

        if not self.dayoff and not self.holiday:
            if ot_fr < self._sched_out():
                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                if self.with_break:
                    overtime -= 1
                if overtime > 0:
                    ot_hrs_list.append([0, 0, {
                        'ot_hours': overtime,
                        'computation_id': self.env.ref('ph_payroll_overtime.ot_regular').id
                    }])
            if ot_to > self._sched_out():
                overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                if overtime > 0:
                    ot_hrs_list.append([0, 0, {
                        'ot_hours': overtime,
                        'computation_id': self.env.ref('ph_payroll_overtime.ot_regular').id
                    }])

        elif self.dayoff and not self.holiday:
            overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
            if ot_fr < self._sched_out():
                if self.with_break:
                    overtime -= 1
                if overtime > 0:
                    ot_hrs_list.append([0, 0, {
                        'ot_hours': overtime,
                        'computation_id': self.env.ref('ph_payroll_overtime.ot_day_off').id
                    }])
            if ot_to > self._sched_out():
                if overtime > 0:
                    overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                    ot_hrs_list.append([0, 0, {
                        'ot_hours': overtime,
                        'computation_id': self.env.ref('ph_payroll_overtime.ot_day_off_ot').id
                    }])

        elif not self.dayoff and self.holiday:
            for h in self.holiday_ids:
                if not h.double_holiday:
                    if h.holiday_type == 'special':
                        if ot_fr < self._sched_out():
                            if ot_to >= self._sched_out():
                                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                            else:
                                overtime = self._compute_ot_hrs(ot_fr, ot_to)

                            if self.with_break:
                                overtime -= 1
                            if overtime > 0:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol').id
                                }])

                        if ot_to > self._sched_out():
                            overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                            if overtime > 0:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol_ot').id
                                }])
                    else:
                        if ot_fr < self._sched_out():
                            if ot_to >= self._sched_out():
                                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                            else:
                                overtime = self._compute_ot_hrs(ot_fr, ot_to)

                            if self.with_break:
                                overtime -= 1
                            if overtime > 0:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol').id
                                }])
                        if ot_to > self._sched_out():
                            overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                            if overtime > 0:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol_ot').id
                                }])
                else:
                    if ot_fr < self._sched_out():
                        if ot_to >= self._sched_out():
                            overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                        else:
                            overtime = self._compute_ot_hrs(ot_fr, ot_to)

                        if self.with_break:
                            overtime -= 1
                        if overtime > 0:
                            ot_hrs_list.append([0, 0, {
                                'ot_hours': overtime,
                                'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol').id
                            }])
                    if ot_to > self._sched_out():
                        overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                        if overtime > 0:
                            ot_hrs_list.append([0, 0, {
                                'ot_hours': overtime,
                                'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol_ot').id
                            }])

        elif self.dayoff and self.holiday:
            for h in self.holiday_ids:
                if not h.double_holiday:
                    if h.holiday_type == 'special':
                        if ot_fr < self._sched_out():
                            if ot_to >= self._sched_out():
                                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                            else:
                                overtime = self._compute_ot_hrs(ot_fr, ot_to)

                            if self.with_break:
                                overtime -= 1
                            if overtime > 0:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol_dayoff').id
                                }])
                        if ot_to > self._sched_out():
                            overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                            if overtime > 0:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_spc_hol_dayoff_ot').id
                                }])
                    else:
                        if ot_fr < self._sched_out():
                            if ot_to >= self._sched_out():
                                overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                            else:
                                overtime = self._compute_ot_hrs(ot_fr, ot_to)

                            if self.with_break:
                                overtime -= 1
                            if overtime > 0:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol_dayoff').id
                                }])
                        if ot_to > self._sched_out():
                            overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                            if overtime > 0:
                                ot_hrs_list.append([0, 0, {
                                    'ot_hours': overtime,
                                    'computation_id': self.env.ref('ph_payroll_overtime.ot_leg_hol_dayoff_ot').id
                                }])
                else:
                    if ot_fr < self._sched_out():
                        if ot_to >= self._sched_out():
                            overtime = self._compute_ot_hrs(ot_fr, self._sched_out())
                        else:
                            overtime = self._compute_ot_hrs(ot_fr, ot_to)
                        if self.with_break:
                            overtime -= 1
                        if overtime > 0:
                            ot_hrs_list.append([0, 0, {
                                'ot_hours': overtime,
                                'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol_dayoff').id
                            }])
                    if ot_to > self._sched_out():
                        overtime = self._compute_ot_hrs(self._sched_out(), ot_to)
                        if overtime > 0:
                            ot_hrs_list.append([0, 0, {
                                'ot_hours': overtime,
                                'computation_id': self.env.ref('ph_payroll_overtime.ot_double_hol_dayoff_ot').id
                            }])

        self.computation_ids = ot_hrs_list