odoo.define('website_recruitment_extend.website', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;

    $('#graduated').on("change", function (event) {
       if ($(this).is(":checked")){
       	$('#edu_graduate_year').show()
       	$('#edu_level_year').hide()
       } else {
       	$('#edu_level_year').show()
       	$('#edu_graduate_year').hide()
       }
    });

    $('#graduated').trigger("change");

});