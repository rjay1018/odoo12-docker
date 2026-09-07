odoo.define('ph_payroll_core.data', function (require) {
"use strict";


var page=require('web.UserMenu');
var usepage=page.include({
    _onMenuSupport: function () {
        window.open('https://www.openhrms.com', '_blank');
    },
    })

});
