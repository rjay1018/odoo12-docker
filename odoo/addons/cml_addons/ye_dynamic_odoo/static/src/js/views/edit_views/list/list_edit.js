odoo.define('ye_dynamic_odoo.ListViewEdit', function (require) {
"use strict";

    var core = require('web.core');
    var Base = require('ye_dynamic_odoo.BaseEdit');
    var ListEditContent = require('ye_dynamic_odoo.ListEditContent');
    var ListEditProperty = require('ye_dynamic_odoo.ListEditProperty');


    var ListViewEdit = Base.EditBase.extend({
        start: function () {
            this._super();
            this.sortData = [["tr, ._wFields", "tr"], ["._wSortable", "tr"]];
            this.view.property = ListEditProperty;
            this.view.content = ListEditContent;
        },
    });

    return ListViewEdit;
});
