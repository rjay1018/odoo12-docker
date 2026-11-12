odoo.define('cml_simplified_vouching.list', function (require) {
'use strict';
var ListController = require('web.ListController');
var ListView = require('web.ListView');
var viewRegistry = require('web.view_registry');

var Controller = ListController.extend({
    buttons_template: 'SimplifiedVouching.buttons',
    renderButtons: function () {
        this._super.apply(this, arguments);
        if (this.$buttons) {
            this.$buttons.on('click', '.o_vouching_refresh', this._onRefresh.bind(this));
        }
    },
    _onRefresh: function () {
        var self = this;
        this._rpc({model: 'simplified.vouching', method: 'refresh', args: []}).then(function () {
            self.reload();
        });
    },
});

viewRegistry.add('simplified_vouching_list', ListView.extend({
    config: _.extend({}, ListView.prototype.config, {Controller: Controller}),
}));
});
