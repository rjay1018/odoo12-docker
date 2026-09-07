odoo.define('ye_dynamic_odoo.GraphViewProperty', function (require) {
"use strict";

    var core = require('web.core');
    var Base = require('ye_dynamic_odoo.BaseEdit');


    var GraphViewProperty = Base.PropertyBase.extend({
        start: function () {
            this._super();
            const {view} = this.property;
            view.graph = {};
            view.graph.graph = [];
        },
        renderTab: function () {},
    });

    return GraphViewProperty;
});
