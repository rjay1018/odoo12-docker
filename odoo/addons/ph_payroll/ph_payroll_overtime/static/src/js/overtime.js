odoo.define('overtime.tree', function (require) {
"use strict";
    var core = require('web.core');
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');
    var Dialog = require('web.Dialog');
    
    var _t = core._t;

    var qweb = core.qweb;

    var OvertimeListController = ListController.extend({
        buttons_template: 'OvertimeView.buttons',

        renderButtons: function () {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                var self = this;
                this.$buttons.on('click', '.o_button_multi_advance_overtime', function () {
                    self.do_action({
                        name: 'Advance Filing',
                        type: 'ir.actions.act_window',
                        res_model: 'hr.advance.overtime',
                        target: 'current',
                        views: [[false, 'form']],
                    }, { on_close: function () {
                            self.trigger_up('reload');
                        },
                    })
                });
            }
        }
    });

    var OvertimeView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: OvertimeListController,
        }),
    });

    viewRegistry.add('overtime_tree', OvertimeView);
});
