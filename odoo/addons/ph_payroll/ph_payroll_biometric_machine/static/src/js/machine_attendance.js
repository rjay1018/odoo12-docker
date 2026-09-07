odoo.define('machine.attendance.tree', function (require) {
"use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var Dialog = require('web.Dialog');
    
    var _t = core._t;

    var qweb = core.qweb;

    var MachineAttendanceListController = ListController.extend({
        buttons_template: 'MachineAttendanceView.buttons',

        renderButtons: function () {
            this._super.apply(this, arguments); // Possibly sets this.$buttons
            if (this.$buttons) {
                var self = this;

                this.$buttons.on('click', '.o_button_download_attendance', function () {
                    Dialog.confirm(self, _t("You are about to download attendance from Biometric device. Select Ok to continue."), {
                        confirm_callback: function () {
                            self._rpc({
                                name: 'Download Attendance',
                                model: 'zk.machine.attendance',
                                method: 'download_attendance',
                                args: [0],
                            }).then(function () {
                                self.trigger_up('reload');
                            })
                        }
                    })
                }),
                
                this.$buttons.on('click', '.o_button_import_attendance', function () {
                    var selectedIDs = self.getSelectedIds();
                    var state = self.model.get(self.handle, {raw: true});
                    var context = state.getContext();
                    context['active_ids'] = selectedIDs;
                    Dialog.confirm(self, _t("This action will import selected records as employee attendance. Select Ok to continue."), {
                        confirm_callback: function () {
                            self._rpc({
                                model: 'zk.machine.attendance',
                                method: 'import_attendance',
                                args: [selectedIDs],
                                context: context
                            }).then(function () {
                                self.trigger_up('reload');
                            })
                        }
                    })
                });


                // this.$buttons.on('click', '.o_button_import_attendance', function () {
                //     var selectedIDs = self.getSelectedIds();
                //     var state = self.model.get(self.handle, {raw: true});
                //     var context = state.getContext();
                //     context['active_ids'] = selectedIDs;
                //     self.do_action({
                //         type: 'ir.actions.act_window',
                //         res_model: 'zk.machine.attendance.import',
                //         target: 'new',
                //         views: [[false, 'form']],
                //         context: context,
                //     }).then(function () {
                //         self.trigger_up('reload');
                //     })
                // });
            }
        }
    });

    var MachineAttendanceView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: MachineAttendanceListController,
        }),
    });

    viewRegistry.add('machine_attendance_tree', MachineAttendanceView);
});
