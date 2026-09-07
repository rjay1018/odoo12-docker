odoo.define('ye_dynamic_odoo.ListEditProperty', function (require) {
"use strict";

    var core = require('web.core');
    var Base = require('ye_dynamic_odoo.BaseEdit');
    var FieldBasic = require('ye_dynamic_odoo.FieldBasic');

    var ListEditProperty = Base.PropertyBase.extend({
        start: function () {
            this._super();
            const {property, view} = this.property;
            delete this.tabs.component;
            // property.color = {label: "Record Color", widget: FieldBasic.ColorLine};
            // property.editable = {label: "Editable", widget: FieldBasic.Checkbox};
            // view.calendar = {};
            // view.calendar.calendar = ["quick_add", "string", "date_start", "date_stop", "date_delay", "all_day", "color", "mode"];
        },
        onPropertyChange: function (node, attr, valChange) {
            if (attr == "color") {
                Object.keys(valChange).map((colorName) => {
                    let val = valChange[colorName], decorationName = "decoration-"+colorName;
                    val ? node.attrs[decorationName] = val : delete node.attrs[decorationName];
                });
                return true;
            }else if ("editable" == attr) {
                if (valChange) {
                    valChange = "bottom";
                } else {
                    delete node.attrs[attr];
                    return true;
                }
            }
            this._super(node, attr, valChange);
        },
        prepareValue: function (attr, value, node) {
            if (attr == "editable" && value) {
                value = true;
            } else if (attr == "color") {
                value = {};
                ["success", "warning", "danger", "primary", "info", "muted", "bf", "it"].map((_attr) => {
                    value[_attr] = node.attrs["decoration-"+_attr] || "";
                });
            }else {
                value = this._super(attr, value, node);
            }

            return value;
        },
    });

    return ListEditProperty;
});
