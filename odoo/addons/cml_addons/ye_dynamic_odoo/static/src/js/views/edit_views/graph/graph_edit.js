odoo.define('ye_dynamic_odoo.GraphViewEdit', function (require) {
"use strict";

    var core = require('web.core');
    var Base = require('ye_dynamic_odoo.BaseEdit');
    var GraphViewContent = require('ye_dynamic_odoo.GraphViewContent');
    var GraphViewProperty = require('ye_dynamic_odoo.GraphViewProperty');


    var GraphViewEdit = Base.EditBase.extend({
        start: function () {
            this._super();
            this.view.property = GraphViewProperty;
            this.view.content = GraphViewContent;
        },

    });

    return GraphViewEdit;
});
