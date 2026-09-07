odoo.define('ye_dynamic_odoo.CalendarViewContent', function (require) {
"use strict";

    var core = require('web.core');
    var CalendarView = require('web.CalendarView');
    var ActionManager = require('web.ActionManager');
    var session = require('web.session');

    var Base = require('ye_dynamic_odoo.BaseEdit');


    var FormEditContent = Base.ContentBase.extend({
        template: 'CalendarViewEdit.Content',
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
            let calendarView = new CalendarView(viewInfo, params);
            let def = $.Deferred();
            calendarView.getController(this).then(function (widget) {
                if (def.state() === 'rejected') {
                    widget.destroy();
                } else {
                    widget.appendTo(self.$el);
                    self.bindAction();
                }
            }).fail(def.reject.bind(def));
        },
    });

    return FormEditContent;

});
