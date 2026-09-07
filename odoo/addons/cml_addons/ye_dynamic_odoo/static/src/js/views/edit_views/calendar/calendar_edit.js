odoo.define('ye_dynamic_odoo.CalendarViewEdit', function (require) {
"use strict";

    var core = require('web.core');
    var Base = require('ye_dynamic_odoo.BaseEdit');
    var CalendarViewContent = require('ye_dynamic_odoo.CalendarViewContent');
    var CalendarViewProperty = require('ye_dynamic_odoo.CalendarViewProperty');


    var FormViewEdit = Base.EditBase.extend({
        start: function () {
            this._super();
            this.view.property = CalendarViewProperty;
            this.view.content = CalendarViewContent;
        },

    });

    return FormViewEdit;
});
