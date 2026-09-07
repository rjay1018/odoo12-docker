odoo.define('ye_dynamic_odoo.form_controller', function(require) {
    var FormController = require('web.FormController');

    FormController.include({
        _onOpenOne2ManyRecord: function(event) {
            event.data.context.useSubView = true;
            this._super(event);
        },
        _onOpenRecord: function(event) {
            event.data.context.useSubView = true;
            this._super(event);
        },
    });
});
