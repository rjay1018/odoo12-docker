odoo.define('ki_survey_extend.button_status', function (require) {
	"use strict";

	require('web.dom_ready');
	var rpc = require('web.rpc');
	var core = require('web.core');
	var _t = core._t;


	$(document).ready(function(){
		$("#button_survey").click(function(ev){
			if ($('#agree').length === 1){
				if($('#agree').is(":checked")){
					return true;
				}
				else{
					ev.preventDefault();
					return false;
				}
			}
			else{
				return true;
			}
		});
	});

});
