odoo.define('ye_dynamic_odoo.form_view', function(require) {
    var FormView = require('web.FormView');

    FormView.include({
        getController: function (parent) {
            this.userContext = this.userContext || {};
            this.userContext.useSubView = true;
            let res = this._super(parent);
            delete this.userContext.useSubView;
            return res
        },
    });
});
