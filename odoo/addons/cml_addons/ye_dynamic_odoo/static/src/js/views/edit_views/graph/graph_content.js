odoo.define('ye_dynamic_odoo.GraphViewContent', function (require) {
"use strict";

    var core = require('web.core');
    var GraphView = require('web.GraphView');
    var ActionManager = require('web.ActionManager');
    var session = require('web.session');

    var Base = require('ye_dynamic_odoo.BaseEdit');


    var GraphViewContent = Base.ContentBase.extend({
        template: 'GraphViewEdit.Content',
        init: function(parent, params) {
            this._super(parent, params);
            this.parent = parent;
        },
        start: function () {
            const {action} = this.props;
            this.action = action;
        },
        bindAction: function () {
        },
        renderView: function () {
            let self = this;
            const {context, domain, limit, res_model, filter} = this.action, {viewInfo} = this.props;
            let params = {
                action: this.action,
                context: context,
                domain: domain || [],
                groupBy: [],
                limit: limit,
                filter: filter || [],
                currentId: undefined,
                disableCustomFilters: undefined,
                footerToButtons: false,
                hasSearchView: true,
                hasSidebar: true,
                headless: false,
                ids: undefined,
                mode: false,
                modelName: res_model,
            };
            let graphView = new GraphView(viewInfo, params);
            let def = $.Deferred();
            graphView.getController(this).then(function (widget) {
                if (def.state() === 'rejected') {
                    widget.destroy();
                } else {
                    widget.renderer.isInDOM = true;
                    widget.appendTo(self.$el);
                    self.bindAction();
                }
            }).fail(def.reject.bind(def));
        },
    });

    return GraphViewContent;

});
