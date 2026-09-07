odoo.define('ye_dynamic_odoo.ListEditContent', function (require) {
"use strict";

    var core = require('web.core');

    var QWeb = core.qweb;
    var Widget = require('web.Widget');
    var _t = core._t;

    var mixins = require('web.mixins');
    var ServicesMixin = require('web.ServicesMixin');
    var Base = require('ye_dynamic_odoo.BaseEdit');


    var EditListRenderer = Widget.extend(ServicesMixin, mixins.EventDispatcherMixin, {
        template: 'ListViewEdit.Content',
        init: function(parent, params) {
            this._super(parent, params);
            this.props = params;
            this.parent = parent;
            this.columns = params.columns || {};
            this.columnsInvisible = params.columnsInvisible || {};
            this.start();
        },
        start: function () {
            this._super();
            this.prepareColumns();
        },
        prepareColumns: function (reload=false) {
            const {viewInfo, columnsInvisible} = this.props, {children} = viewInfo.arch || {}, ckInvisible = ["1", 1, true, 'True'];
            let count = 0;
            if (reload) {
                this.columns = {};
                this.columnsInvisible = columnsInvisible || {};
            }
            (children || []).map((field) => {
                const {tag} = field, {invisible, modifiers, name} = field.attrs;
                if (tag === 'field') {
                    ckInvisible.includes(invisible) || (modifiers && ckInvisible.includes((modifiers.invisible || modifiers.column_invisible)))
                        ? this.columnsInvisible[name] = field : (count += 1, field.sequence = count, this.columns[name] = field);
                }
            });
        },
        setModifiers: function (node, el) {
            const {name} = node.attrs;
            if (name in this.columnsInvisible) {
                el.addClass("o_invisible_modifier");
            }
        },
        _reloadNode: function (nodeId) {
            this.prepareColumns();
            this.renderView();
        },
        _renderNode: function (node) {
            if (node.tag == "field") {
                this.parent.setNodeId(node);
                let {name} = node.attrs, params = {string: this.parent.getNodeAttr(node, "string"), name: name, class: ""};
                const {viewInfo} = this.props, {fieldsInfo, fields, type} = viewInfo;
                const field = fields[name] || fieldsInfo[type][name];
                params.class = ["float", "int", "monetary"].includes(field.type) ? "_colNo" : "_colStr";
                switch (node.attrs.widget) {
                    case "handle":
                        params.string = "";
                        params.isHandle = true;
                        params.class += " _colHandle";
                        break;
                }
                let elNode = $(QWeb.render("ListViewEdit.Content.Col", params));
                elNode.attr({'node-id': node.nodeId});
                this.setModifiers(node, elNode);
                return elNode;
            }
        },
        renderView: function () {
            const {viewInfo} = this.props, {fields} = viewInfo, {children} = viewInfo.arch || {};
            if (children) {
                const {showInvisible} = viewInfo.arch.attrs;
                this.$el.find("table tr").empty().append(children.map((node) => (this._renderNode(node))));
                this.parent.setNodeId(viewInfo.arch);
                this.$el.attr({'node-id': viewInfo.arch.nodeId});
                this.$el[showInvisible ? "addClass" : "removeClass"]("showInvisible");
            }
        },
        renderElement: function () {
            this._super();
            this.renderView();
        },
    });

    var ListEditContent = Base.ContentBase.extend({
        init: function(parent, params) {
            const {parentRecord} = params.viewInfo;
            this.parentRecord = parentRecord || {};
            this.ref = {};
            this._super(parent, params);
        },
        start: function () {
            this._super();
            this._processColumnInvisibleFields();
            this.columnDomainInvisible = this._evalColumnInvisibleFields();
        },
        _prepareParamContent: function () {
            let res = this._super();
            res.columnsInvisible = this.columnDomainInvisible;
            return res;
        },
        reloadNode: function (nodeId) {
            this.ref.content._reloadNode(nodeId);
            this.bindAction();
        },
        _processColumnInvisibleFields: function () {
            var columnInvisibleFields = {};
            const {viewInfo} = this.props;
            _.each(viewInfo.columnInvisibleFields, function (domains, fieldName) {
                if (_.isArray(domains)) {
                    columnInvisibleFields[fieldName] = _.map(domains, function (domain) {
                        if (_.isArray(domain)) {
                            return [domain[0].split('.')[1]].concat(domain.slice(1));
                        }
                        return domain;
                    });
                }
            });
            this.columnInvisibleFields = columnInvisibleFields;
        },
        _evalColumnInvisibleFields: function () {
            var self = this;
            return _.mapObject(this.columnInvisibleFields, function (domains) {
                    return self.parentRecord.evalModifiers({
                    column_invisible: domains,
                 }).column_invisible;
            });
        },
        onClickNode: function (e) {
            e.stopPropagation();
            const {onClickNode} = this.props;
            let nodeEl = $(e.currentTarget), nodeId = nodeEl.attr("node-id");
            if (nodeId && nodeId in this.nodes) {
                let node = this.nodes[nodeId];
                onClickNode(node);
                this.$el.find(".nodeActive").removeClass("nodeActive");
                nodeEl.addClass("nodeActive");
            }
        },
        onRemoveNode: function (node) {
            let el = false, nodeId = false
            if (typeof node == "string") {
                el = this.findNode(node);
                nodeId = node;
            }else {
                node.stopPropagation();
                el = $(node.currentTarget).parents("th[node-id]");
                nodeId = el.attr("node-id");
            }
            this.xpathToNode(nodeId, false, el.parents("[node-id]").attr("node-id"), false, "replace");

        },
        bindAction: function () {
            const {bindSortable} = this.props;
            this.$el.find("[node-id]").click(this.onClickNode.bind(this));
            this.$el.find("._sCl").click(this.onRemoveNode.bind(this));
            bindSortable(this.$el);
        },
        renderView: function () {
            this.ref.content = new EditListRenderer(this, {...this.props, columnsInvisible: this.columnDomainInvisible});
            this.ref.content.renderElement();
            this.$el.empty().append(this.ref.content.$el);
            this.bindAction();
        }
    });

    return ListEditContent;

});
