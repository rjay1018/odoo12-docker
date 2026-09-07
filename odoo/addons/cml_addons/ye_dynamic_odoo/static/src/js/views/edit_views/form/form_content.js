odoo.define('ye_dynamic_odoo.FormEditContent', function (require) {
"use strict";

    var core = require('web.core');
    var FieldBasic = require('ye_dynamic_odoo.FieldBasic');
    var FormRenderer = require('web.FormRenderer');
    var ListViewEdit = require('ye_dynamic_odoo.ListViewEdit');

    var QWeb = core.qweb;
    var Base = require('ye_dynamic_odoo.BaseEdit');
    var Context = require('web.Context');


    var EditFormRenderer = FormRenderer.extend({
        init: function (parent, state, props) {
            this._super(parent, state, props);
            this.props = props;
            this.parent = parent || {};
            this.nodes = this.parent.nodes;
            this.ref = {node: {}};
        },
        start: function () {
            this.$el.addClass('_formEdit');
            return this._super.apply(this, arguments);
        },
        _addOnClickAction: function () {},
        _postProcessField: function (widget, node) {
            this._super(widget, node);
            const {fields, fieldsInfo} = this.state, fieldName = node.attrs.name;
            const field = fields[fieldName] || fieldsInfo.form[fieldName];
            if (field.type == "many2one") {
                widget.$el.removeAttr("href");
                widget._onClick = () => {}
            }
        },
        _reloadNode: function (nodeId) {
            let fieldNode = this.nodes[nodeId], parentId = fieldNode.parentId;
            if (fieldNode.tag == "form") {
                this._renderView();
                return true;
            }
            if (parentId in this.nodes) {
                let parentNode = this.nodes[parentId];
                switch (parentNode.tag) {
                    case "group":
                        nodeId = parentId;
                        fieldNode = parentNode;
                        if (parentNode.parentId) {
                            let stopCheck = false;
                            while (!stopCheck) {
                                let _parentNode = this.nodes[parentNode.parentId];
                                if (_parentNode.tag !== 'group') {
                                    nodeId = parentNode.nodeId;
                                    fieldNode = parentNode;
                                    stopCheck = true;
                                } else {
                                    if (_parentNode.parentId) {
                                        parentNode = _parentNode;
                                    } else {
                                        nodeId = _parentNode.nodeId;
                                        fieldNode = _parentNode;
                                        stopCheck = true;
                                    }
                                }
                            }
                        }
                        break;
                    case "notebook":
                        nodeId = parentId;
                        fieldNode = parentNode;
                        break;
                }
            }
            this.allModifiersData = [];
            this.parent.findNode(nodeId).replaceWith(this._renderNode(fieldNode));
        },
        _renderNode: function (node) {
            this.parent.setNodeId(node);
            let res = this._super(node);
            if (node.nodeId) {
                res.attr({'node-id': node.nodeId});
            }
            return res;
        },
        _renderChild: function (children, wrap) {
            children.map((child) => {
                wrap.append(this._renderNode(child));
            });
        },
        _renderTagNotebook: function (node) {
            this.parent.setNodeId(node);
            let self = this, tabs = {}, oldRef = this.ref.node[node.nodeId];
            node.children.map((page) => {
                const {string} = page.attrs, name = page.attrs.name || "page_" + this.parent.getRandom();
                let modifiers = self._registerModifiers(page, this.state);
                if (!modifiers.invisible) {
                    self.parent.setNodeId(page);
                    page.parentId = node.nodeId;
                    page.attrs.name = name;
                    tabs[name] = {label: string, name: name, render: (() => this._renderNode(page)).bind(this), fieldNode: page};
                }
            });
            let wrapNode = new FieldBasic.Tab(this, {tabs: tabs, fieldNode: node, data: oldRef ? oldRef.state.data : Object.keys(tabs)[0],
                onClickTab: this.parent.onClickTab.bind(this.parent), onAddTab: this.parent.onAddTab.bind(this.parent), add: true});
            wrapNode.renderElement();
            this.ref.node[node.nodeId] = wrapNode;
            return wrapNode.$el;
        },
        _renderTagPage: function (node) {
            let wrapNode = $(QWeb.render("Form.TagPage", {}));
            this._renderChild(node.children, wrapNode);
            this._handleAttributes(wrapNode, node);
            this._registerModifiers(node, this.state, wrapNode);
            return wrapNode;
        },
        _renderInnerGroup: function (node) {
            let res = this._super(node);
            node.children.map((child) => {
                if (child.tag) {
                    child.parentId = node.nodeId;
                }
            });
            if (node.attrs.string) {
                res.find("tr:first-child").addClass("_rowSeparator");
            }
            res.addClass("_wGroupInner");
            res.find("> t_body > tr".replace("_", "")).each((idx, el) => {
                let childVisible = $(el).find("> td > *").filter((_idx, _el) => !$(_el).hasClass("o_invisible_modifier"));
                if (!childVisible.length) {
                    $(el).addClass("_rowInvisible");
                }
            });
            if (!node.children.length) {
                let $trPlace = $('<tr class="_noSort">').append('<td>');
                res.find("tr:last-child").after($trPlace);
            }
            return res;
        },
        _renderOuterGroup: function (node) {
            let res = this._super(node);
            node.children.map((child) => {
               child.parentId = node.nodeId;
            });
            return res;
        },
        _renderInnerGroupField: function (node) {
            let res = this._super(node);
            this.parent.setNodeId(node);
            res.find(" > *").attr({"node-id": node.nodeId});
            return res;
        },
        _renderHeaderButton: function (node) {
            let res = this._super(node);
            this.parent.setNodeId(node);
            res.addClass("_olEdit").attr({"node-id": node.nodeId});
            return res;
        },
        _renderInnerGroupLabel: function (node) {
            let res = this._super(node);
            this.parent.setNodeId(node);
            res.find(" > *").attr({"node-id": node.nodeId});
            return res;
        },
        _renderWrapAb: function (views) {
            let el = QWeb.render("Edit.wrapAb", {views: [{type: "list", label: "Edit List"},
                    {type: "form", label: "Edit Form"}].filter((view) => view.type in views)});
            return el;
        },
        _renderFieldWidget: function (node, state) {
            const {fields, fieldsInfo, viewType} = this.state,
                {name, widget} = node.attrs, field = fields[name], fieldInfo = fieldsInfo[viewType][name];
            let res = this._super(node, state), widgetName = (widget || field.type);
            res.addClass("_olEdit");
            if (fieldInfo.views && Object.keys(fieldInfo).length) {
                res.append(this._renderWrapAb(fieldInfo.views))
            }
            return res;
        },
        _renderTagLabel: function (node) {
            let res = this._super(node);
            if (node.tag == 'label') {
                res.addClass("_olEdit");
            }
            return res;
        },
        _updateView: function ($newContent) {
            let formNodeId = $newContent.parents(".o_form_view").attr("node-id");
            if (formNodeId) {
                let showInvisible = this.nodes[formNodeId].attrs.showInvisible, checkVal = ["true", true, "True", 1];
                this.$el.attr({"node-id": formNodeId});
                this.$el[checkVal.includes(showInvisible) ? "addClass" : "removeClass"]("showInvisible");
            }
            this._super($newContent);
            this.parent.bindAction();
        },
        _render: function () {
            this._super();
        }
    });

    var FormEditContent = Base.ContentBase.extend({
        template: 'FormViewEdit.Content',
        init: function(parent, params) {
            this._super(parent, params);
            this.parent = parent;
        },
        start: function () {
            this._super();
            const {viewInfo, controller, action} = this.props, {fields, fieldsInfo, model, parentId} = viewInfo;
            // this.controlRenderer = controller.renderer;
            this.viewState = false;

            // if ((controller || {}).renderer) {
            //     const viewType = controller.viewType;
            //     if (viewType === "form") {
            //         this.viewState = controller.renderer.state;
            //         this.viewState.fieldsInfo = fieldsInfo;
            //     }
            // }
            const state = $.bbq.getState(true);
            if (!this.viewState) {
                this.loadParams = {
                    context: action.context || {},
                    count: 0,
                    data: {},
                    domain: [],
                    timeRange: [],
                    timeRangeDescription: "",
                    comparisonTimeRange: [],
                    comparisonTimeRangeDescription: "",
                    compare: false,
                    fields: {...fields},
                    fieldsInfo: {...fieldsInfo},
                    groupedBy: [],
                    modelName: model,
                    res_id: state.id || undefined,
                    id: model + "_40",
                    res_ids: [state.id],
                    parentID: parentId || undefined,
                    type: "record",
                    viewType: "form",
                    orderedBy: undefined,
                };
            }
        },
        bindAction: function () {
            const {bindSortable} = this.props;
            this.$el.find("[node-id], ._wGroupInner tr").click(this.onClickNode.bind(this));
            this.$el.find("._subEditList").click(this.openSubView.bind(this));
            this.$el.find("._subEditForm").click(this.openSubView.bind(this));
            bindSortable(this.$el);
        },
        onClickNode: function (e) {
            e.stopPropagation();
            const {onClickNode} = this.props;
            let nodeEl = $(e.currentTarget), nodeId = nodeEl.attr("node-id");
            if (!nodeId && nodeEl[0].localName == "tr") {
                nodeId = nodeEl.find("> td:not(.o_td_label) > *[node-id]").attr("node-id");
                if (!nodeId) {
                    nodeId = nodeEl.find("> td > *[node-id]").attr("node-id");
                }
            }
            if (nodeId && nodeId in this.nodes) {
                let node = this.nodes[nodeId];
                onClickNode(node);
                this.$el.find(".nodeActive").removeClass("nodeActive");
                nodeEl.addClass("nodeActive");
            }
        },
        onClickTab: function () {
            this.bindAction();
        },
        onAddTab: function (nodeId) {
            if (nodeId) {
                this.nodes[nodeId].children.push(this.getNewPage());
                this.reloadNode(nodeId);
            }
        },
        onRemoveNode: function (nodeId) {
            let el = this.findNode(nodeId);
            this.xpathToNode(nodeId, false, el.parents("[node-id]").attr("node-id"), false, "replace");
        },
        getNewFieldData: function (widget) {
            let data = null;
            switch (widget) {
                case "char":
                case "text":
                    data = "";
                    break;
                case "date":
                case "datetime":
                    data = false;
                    break;
                case "integer":
                case "float":
                case "monetary":
                    data = 0;
                    break;
                case "boolean":
                    data = false;
                    break;
                case "many2many":
                case "one2many":
                    data = [];
                    break;
                default:
                    data = "";
                    break;
            }
            return data;
        },
        _processNewNode: function (node) {
            this._super(node);
            const {name, widget} = node.attrs;
            this.viewState.data[name] = this.getNewFieldData(widget);
        },
        openSubView: function (e) {
            e.stopPropagation();
            e.stopImmediatePropagation();
            const {showSubView} = this.props;
            let el = $(e.currentTarget), viewType = el.attr("viewType"), nodeId = el.parents("[node-id]").attr("node-id");
            if (showSubView && nodeId in this.nodes && viewType) {
                const node = this.nodes[nodeId], {fieldsInfo, fields} = this.viewState,
                    fieldInfo = fieldsInfo.form[node.attrs.name], viewInfo = fieldInfo.views[viewType], field = fields[node.attrs.name];
                viewInfo.model = field.relation;
                viewInfo.parentId = this.viewState.id;
                viewInfo.parentRecord = this.viewState;
                viewInfo.columnInvisibleFields = fieldInfo.columnInvisibleFields || {};
                showSubView(node, viewInfo);
            }
        },
        closeSubView: function (nodeId, viewType) {
            const node = this.nodes[nodeId], {fieldsInfo} = this.viewState,
                viewInfo = fieldsInfo.form[node.attrs.name].views[viewType];
            const subViewData = this.viewState.data[node.attrs.name];
            if (subViewData.type == viewType) {
                const fieldsSubView = subViewData.fields, fieldsInfoSubView = subViewData.fieldsInfo[viewType], fieldAppear = {};
                // set new field to record fields
                Object.keys(viewInfo.fields).filter((fieldName) => !(fieldName in fieldsSubView)).map((fieldName) => {
                    fieldAppear[fieldName] = viewInfo.fields[fieldName];
                    fieldsSubView[fieldName] = fieldAppear[fieldName];
                });
                // reset new field to record list
                if (subViewData.data && subViewData.data.length && Object.keys(fieldAppear).length) {
                    subViewData.data.map((dataLine) => {
                        for (var fName in fieldAppear) {
                            dataLine.fields[fName] = fieldAppear[fName];
                        }
                    });
                }
                // set new field to record fieldsInfo
                Object.values(viewInfo.fieldsInfo[viewType]).filter((field) => !(field.name in fieldsInfoSubView)).map((field) => {
                    fieldsInfoSubView[field.name] = field;
                });
            }
        },
        getMailFields: function () {
            var mailFields = {}, mailWidgets = ['mail_followers', 'mail_thread', 'mail_activity', 'kanban_activity'];
            let fieldsInfo = this.viewState.fieldsInfo['form'];
            for (var fieldName in fieldsInfo) {
                var fieldInfo = fieldsInfo[fieldName];
                if (_.contains(mailWidgets, fieldInfo.widget)) {
                    mailFields[fieldInfo.widget] = fieldName;
                    fieldInfo.__no_fetch = true;
                }
            }
            return mailFields;
        },
        loadFieldGet: function (modelName) {
            return this['_rpc']({
                model: 'odo.studio',
                method: 'load_field_get',
                args: [modelName],
                kwargs: {},
            });
        },
        _loadSubviews: function () {
            let self = this, def = [];
            const {fields, fieldsInfo, viewFields, base_model} = this.props.viewInfo, _fieldsInfo = fieldsInfo['form'];
            Object.values(_fieldsInfo).filter((field) => field.name in fields && ['one2many', 'many2many'].includes(fields[field.name].type)).map((field) => {
                let viewNeed = ["form", "list"].filter(
                    (viewType) => !Object.keys(field.views || {}).includes(viewType)).map(
                        (viewType) => [null, viewType]);
                Object.keys(field.views || {}).map((viewType) => {
                    if (["form", "list"].includes(viewType)) {
                        def.push(self.loadFieldGet(viewFields[field.name].relation).then(function (fieldsGet) {
                            field.views[viewType].fieldsGet = fieldsGet;
                        }));
                    }
                });
                if (field.Widget.prototype.useSubview && !field.__no_fetch && viewNeed.length) {
                    let context = {...this.getSession().user_context, useSubView: true}, regex = /'([a-z]*_view_ref)' *: *'(.*?)'/g, matches;
                    while (matches = regex.exec(field.context)) {
                        context[matches[1]] = matches[2];
                    }
                    let refinedContext = _.pick(self.loadParams ? self.loadParams.context : self.viewState.context, function (value, key) {
                        return key.indexOf('_view_ref') === -1;
                    });
                    refinedContext.base_model_name = base_model;

                    def.push(self.loadViews(fields[field.name].relation, new Context(context, refinedContext).eval(), viewNeed)
                        .then(function (views) {
                            for (var viewName in views) {
                                field.views[viewName] = self.getParent()._processFieldsView(views[viewName], viewName);
                                field.views[viewName].fields = field.views[viewName].viewFields;
                            }
                        }));
                }
            });
            return $.when.apply($, def);
        },
        reloadNode: function (nodeId) {
            this.ref.content._reloadNode(nodeId);
            this.bindAction();
        },
        _renderView: function () {
            const {viewInfo, controller} = this.props;
            const {activeActions, mailFields, noContentHelp} = (controller || {}).renderer || {};
            this.ref.content = new EditFormRenderer(this, this.viewState, {
                ...this.props,
                activeActions: activeActions || {edit: false},
                arch: viewInfo.arch,
                mode: "readonly",
                mailFields: mailFields || this.getMailFields(),
                noContentHelp: noContentHelp || false,
                viewType: viewInfo.type,
            });
            this.ref.content.appendTo(this.$el.find("._wFormCon")).then(() => {
            });
            this.bindAction();
        },
        renderView: function () {
            let self = this;
            const {editView} = this.props;
            this._loadSubviews().then(function () {
                if (self.viewState) {
                    self._renderView();
                }else {
                    editView.model.load(self.loadParams).then((result) => {
                        self.viewState = editView.getViewState(result);
                        self._renderView()
                    });
                }
            })
        }
    });

    return FormEditContent;

});
