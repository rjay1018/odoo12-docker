odoo.define('ye_dynamic_odoo.PivotViewContent', function (require) {
"use strict";

    var core = require('web.core');
    // var FieldBasic = require('odoo_dynamic.FieldBasic');
    // var FormRenderer = require('web.FormRenderer');
    // var ListViewEdit = require('odoo_dynamic.ListViewEdit');
    var PivotView = require('web.PivotView');
    var ActionManager = require('web.ActionManager');
    var session = require('web.session');

    var QWeb = core.qweb;
    var Base = require('ye_dynamic_odoo.BaseEdit');
    var Context = require('web.Context');


    var PivotEditContent = Base.ContentBase.extend({
        template: 'PivotViewEdit.Content',
        init: function(parent, params) {
            this._super(parent, params);
            this.parent = parent;
        },
        start: function () {
            const {action} = this.props;
            this.action = action;
        },
        bindAction: function () {
        },
        renderView: function () {
            let self = this;
            const {context, domain, limit, res_model, filter} = this.action, {viewInfo} = this.props;
            let params = {
                action: this.action,
                context: context,
                domain: domain || [],
                groupBy: [],
                limit: limit,
                filter: filter || [],
                modelName: res_model,
            };
            let pivotView = new PivotView(viewInfo, params);
            let def = $.Deferred();
            pivotView.getController(this).then(function (widget) {
                if (def.state() === 'rejected') {
                    widget.destroy();
                } else {
                    widget.appendTo(self.$el);
                    self.bindAction();
                }
            }).fail(def.reject.bind(def));
        },
    });

    return PivotEditContent;

});
