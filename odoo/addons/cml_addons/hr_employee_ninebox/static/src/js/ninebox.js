odoo.define('mytest.ninebox', function (require) {
    'use strict';
    
    var AbstractField = require('web.AbstractField');
    var field_registry = require('web.field_registry');    
    var core = require('web.core');
    var QWeb = core.qweb;

    // var basic_fields = require('web.basic_fields');
    // var FieldChar = basic_fields.FieldChar;
    // var NineBox = AbstractField.extend(

    var NineBox = AbstractField.extend({        
        init: function () {
            this._super.apply(this, arguments);
        },
        start: function() {
            return this._super();
        },        
        renderElement: function() {
            var self =  this;
            this._super();
            var ratio = '0X0';
            if (this.value == '0X0') {
                ratio = '0X0';
            } 
            else if (this.value == '0X1') {
                ratio = '0X0';
            } 
            else if (this.value == '0X2') {
                ratio = '0X0';
            } 
            else if (this.value == '0X3') {
                ratio = '0X0';
            } 
            else if (this.value == '1X0') {
                ratio = '0X0';
            } 
            else if (this.value == '2X0') {
                ratio = '0X0';
            } 
            else if (this.value == '3X0') {
                ratio = '0X0';
            } 
            else {
                ratio = this.value;
            }
            this.$el.html(QWeb.render("NineBox", {ratio: ratio}));
        },
    })
    field_registry.add('ninebox', NineBox);
    return NineBox;
});