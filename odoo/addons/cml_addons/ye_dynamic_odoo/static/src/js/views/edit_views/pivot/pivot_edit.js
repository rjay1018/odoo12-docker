odoo.define('ye_dynamic_odoo.PivotViewEdit', function (require) {
"use strict";

    var core = require('web.core');
    var Base = require('ye_dynamic_odoo.BaseEdit');
    var PivotViewContent = require('ye_dynamic_odoo.PivotViewContent');
    var PivotViewProperty = require('ye_dynamic_odoo.PivotViewProperty');


    var FormViewEdit = Base.EditBase.extend({
        start: function () {
            this._super();
            // this.sortData = [["._wGroupInner > tbody", "._wGroupInner > tbody"]
            //     , ["._wComTag ._wSortable,.o_form_sheet,.o_form_nosheet,._wPage", ".o_form_sheet,.o_form_nosheet,._wPage"],
            //     , ["._wComField ._wSortable", "._wGroupInner > tbody"],
            //     , ["._wFields", "._wGroupInner > tbody"],
            // ];
            // this.useSubProp = false;
            this.view.property = PivotViewProperty;
            this.view.content = PivotViewContent;
        },

    });

    return FormViewEdit;
});
