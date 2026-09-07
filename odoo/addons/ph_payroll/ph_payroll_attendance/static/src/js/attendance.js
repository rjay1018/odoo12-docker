odoo.define('emp.dtr.tree', function (require) {
"use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var Dialog = require('web.Dialog');
    
    var _t = core._t;

    var qweb = core.qweb;

    var EmployeeDTRListController = ListController.extend({
        buttons_template: 'EmployeeDTRView.buttons',

        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_multiple_dtr', function () {
                    self.do_action({
                        name: 'Multiple DTR',
                        type: 'ir.actions.act_window',
                        res_model: 'multiple.dtr',
                        target: 'new',
                        views: [[false, 'form']],
                    }, { on_close: function () {
                            self.trigger_up('reload');
                        },
                    })
                });
            }
        }
    });

    var EmployeeDTRView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: EmployeeDTRListController,
        }),
    });

    viewRegistry.add('emp_dtr_tree', EmployeeDTRView);
});



odoo.define('emp.attendance.tree', function (require) {
"use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var Dialog = require('web.Dialog');
    
    var _t = core._t;

    var qweb = core.qweb;

    var EmployeeAttendanceListController = ListController.extend({
        buttons_template: 'EmployeeAttendanceView.buttons',

        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_multiple_attendance', function () {
                    self.do_action({
                        name: 'Multiple Attendance',
                        type: 'ir.actions.act_window',
                        res_model: 'multiple.attendance',
                        target: 'new',
                        views: [[false, 'form']],
                    }, { on_close: function () {
                            self.trigger_up('reload');
                        },
                    })
                });

                this.$buttons.on('click', '.o_button_multi_ot_request', function () {
                    var selectedIDs = self.getSelectedIds();
                    var state = self.model.get(self.handle, {raw: true});
                    var context = state.getContext();
                    context['active_ids'] = selectedIDs;
                    self.do_action({
                        type: 'ir.actions.act_window',
                        res_model: 'ot.request.multi',
                        target: 'new',
                        views: [[false, 'form']],
                        args: [selectedIDs],
                        context: context
                    }, { on_close: function () {
                            self.trigger_up('reload');
                        },
                    })
                });

            }
        }
    });

    var EmployeeAttendanceView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: EmployeeAttendanceListController,
        }),
    });

    viewRegistry.add('emp_att_tree', EmployeeAttendanceView);
});
