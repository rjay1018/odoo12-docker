odoo.define('ye_dynamic_odoo.AbstractController', function (require) {
"use strict";

    var core = require('web.core');
    var AbstractController = require('web.AbstractController');
    var AbstractView = require('web.AbstractView');
    var EditView = require('ye_dynamic_odoo.EditView');

    var QWeb = core.qweb;


    AbstractController.include({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.fieldsView = params.fieldsView || {};
            this._processFieldsView = params._processFieldsView || false;
        },
        _renderSwitchButtons: function () {
            let res = this._super();
            this._renderEditMode(res);
            return res;
        },
        _renderEditMode: function (container) {
            let $editMode = $(QWeb.render("EditView.iconMore", this));
            container.push($editMode[0]);
            $editMode.click(() => {
                let newView = new EditView(this,
                    // {_makeDefaultRecord: this.model._makeDefaultRecord.bind(this.model),
                    {modelName: this.modelName});
                newView.renderElement();
                this.getParent().$el.after(newView.$el);
            });
        }

    });

    AbstractView.include({
        init: function (viewInfo, params) {
            this._super(viewInfo, params);
            this.controllerParams.fieldsView = this.fieldsView;
            this.controllerParams._processFieldsView = this._processFieldsView.bind(this);
        }
    });
});
