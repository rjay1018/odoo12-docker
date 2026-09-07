odoo.define('ye_dynamic_odoo.CalendarViewProperty', function (require) {
"use strict";

    var core = require('web.core');
    var Base = require('ye_dynamic_odoo.BaseEdit');
    var FieldBasic = require('ye_dynamic_odoo.FieldBasic');


    var FormEditProperty = Base.PropertyBase.extend({
        start: function () {
            this._super();

            const {property, view} = this.property;
            delete property.color;
            property.date_start = {label: "Date Start", widget: FieldBasic.Selection};
            property.date_stop = {label: "Date Stop", widget: FieldBasic.Selection};
            property.date_delay = {label: "Date Delay", widget: FieldBasic.Selection};
            property.quick_add = {label: "Quick Add", widget: FieldBasic.Checkbox, default: true};
            property.all_day = {label: "All Day", widget: FieldBasic.Selection};
            property.color = {label: "Color", widget: FieldBasic.Selection};
            property.mode = {label: "Default Display Mode", widget: FieldBasic.Selection};
            view.calendar = {};
            view.calendar.calendar = ["quick_add", "string", "date_start", "date_stop", "date_delay", "all_day", "color", "mode"];
            this.preparePropertyInfo();
        },
        preparePropertyInfo: function () {
            const {viewInfo} = this.props, data = {date_start: [], date_stop: [], date_delay: [], color: [], all_day: []}, {fieldsGet} = viewInfo;
            for (let [key, value] of Object.entries(fieldsGet)) {
                let item = {label: value.string, value: key}
                if (["float", "integer", "monetary"].includes(value.type)) {
                    data.date_delay.push(item);
                }else if (["many2one", "selection"].includes(value.type)) {
                    data.color.push(item);
                }else if (["datetime", "date"].includes(value.type)) {
                    data.date_start.push(item);
                    data.date_stop.push(item);
                }else if ("boolean" == value.type) {
                    data.all_day.push(item);
                }
            }
            data.mode = [{value: 'day', label: 'Day'}, {value: 'week', label: 'Week'}, {value: 'month', label: 'Month'}];
            Object.keys(data).map((propName) => {
                this.property.property[propName].props = {data: data[propName]}
            });
            return data;
        },
        renderTab: function () {},
        renderElement: function () {
            const {viewInfo} = this.props;
            this._super();
            this.renderProperty(viewInfo.arch);
        },
    });

    return FormEditProperty;
});
