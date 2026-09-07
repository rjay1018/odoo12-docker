odoo.define('ye_dynamic_odoo.EditView', function (require) {
"use strict";

    var core = require('web.core');
    var FormViewEdit = require("ye_dynamic_odoo.FormViewEdit");
    var CalendarEdit = require("ye_dynamic_odoo.CalendarViewEdit");
    var PivotViewEdit = require("ye_dynamic_odoo.PivotViewEdit");
    var ListViewEdit = require("ye_dynamic_odoo.ListViewEdit");
    var GraphViewEdit = require("ye_dynamic_odoo.GraphViewEdit");
    // var KanbanViewEdit = require("ye_dynamic_odoo.KanbanViewEdit");

    var BasicModel = require('web.BasicModel');

    var mixins = require('web.mixins');
    var BasicView = require('web.BasicView');
    var ActionManager = require('web.ActionManager');
    var session = require('web.session');

    var QWeb = core.qweb;
    var Widget = require('web.Widget');

    var EditBasicView = BasicView.extend({
        init: function (parent, params) {}
    });

    var EditViewModel = BasicModel.extend({
        createNewView: function (data) {
            return this._rpc({
                model: "odo.studio",
                method: 'create_new_view',
                args: [data],
                kwargs: {},
            });
        },
        onActionView: function (data, save=true) {
            this._rpc({
                model: data.model,
                method: save ? 'store_view' : 'undo_view',
                args: [data.data],
                kwargs: {},
            }).then(function (result) {
                alert("Successfully");
                location.reload();
            });
        },
        onStoreView: function (data) {
            this.onActionView(data);
        },
        onUndoView: function (data) {
            this.onActionView(data, false);
        }
    });

    var EditView = Widget.extend(mixins.EventDispatcherMixin, {
        template: 'EditView',
        events: {
            'click ._headEdit .fa-close': 'onClose',
            'click ._headEdit .fa-minus': 'onMinus',
            'click ._headEdit .fa-expand': 'onExpand',
            'click ._aSave': 'onSaveView',
            'click ._aUndo': 'onRemoveView',
            'click ._aRemove': 'onRemoveNode',
            'click ._aStore': '_onStoreToDatabase',
        },
        init: function(parent, params) {
            this._super(parent);
            this.props = params;
            this.controller = parent;
            this.start();
        },
        start: function () {
            this.ref = {};
            this.basicView = new EditBasicView(this, {});
            this.model = new EditViewModel(this);
            this._processFieldsView = this.basicView._processFieldsView.bind(this.basicView);
            this.viewsInfo = {form: {widget: FormViewEdit, label: "FormView", icon: "fa-wpforms", subView: {form: {widget: FormViewEdit}, list: {widget: ListViewEdit}}},
                              list: {widget: ListViewEdit, label: "ListView", icon: "fa-list-ul"},
                              // kanban: {widget: KanbanViewEdit, label: "Kanban", icon: "fa-th-large"},
                              calendar: {widget: CalendarEdit, label: "Calendar", icon: "fa-calendar"},
                              pivot: {widget: PivotViewEdit, label: "Pivot", icon: "fa-th"},
                              graph: {widget: GraphViewEdit, label: "KanBan", icon: "fa-bar-chart"},
            };
            const viewType = this.controller.viewType;
            this.state = {viewType: viewType in this.viewsInfo ? viewType : "list"};
        },
        setState: function (params) {
            Object.keys(params).map((key) => {
                this.state[key] = params[key];
            });
        },
        _makeDefaultRecord: function (modelName, params) {
            const {res_model} = this.action;
            return this.model._makeDefaultRecord(modelName || res_model, params);
        },
        onClose: function () {
            this.$el.remove();
        },
        onMinus: function () {
            this.$el.hasClass("minus") ? this.$el.removeClass("minus") : this.$el.addClass("minus");
        },
        onExpand: function () {
            this.$el.hasClass("expand") ? this.$el.removeClass("expand") : this.$el.addClass("expand");
        },

        onSaveView: function () {
            this.model.onStoreView(this.getViewData());
        },
        onRemoveView: function () {
            this.model.onUndoView(this.getViewData());
        },
        onClickView: function (viewType) {
            this.setState({viewType: viewType});
            this._switchView();
        },
        onRemoveNode: function (e) {
             e.stopPropagation();
            this.ref.view.onRemoveNode();
        },
        createNewView: function () {
            return this.model.createNewView(this.prepareNewView());
        },
        bindStyle: function () {
            $(".o_content").addClass("_overHide");
        },
        bindAction: function () {
            this.$el.find("._wSubView").click(this.closeSubView.bind(this));
            this.$el.find("._aRemove").click(this.onRemoveNode.bind(this));
        },
        getViewState: function (viewId) {
            return this.model.get(viewId)
        },
        getViewData: function () {
            const params = {};
            if (this.ref.subView) {
                const {viewInfo, nodeId} = this.ref.subView, type = viewInfo.type;
                params.model = "odo.studio.sub_view";
                params.data = this.ref.view.getSubViewData(nodeId, type);
                if (type == "form") {
                    params.data.model_name = viewInfo.model;
                    params.data.new_fields = this.ref.subView.prepareNewField();
                }
            }else {
                params.model = "odo.studio";
                params.data = this.ref.view.getData()
            }
            return params;
        },
        getViewInfo: function () {
            let self = this;
            const {viewType} = this.state;
            if (viewType in self.fieldsViews) {
                let viewInfo = this._processFieldsView(self.fieldsViews[viewType], viewType);
                return  {...viewInfo, fields: {...viewInfo.fields}};
            }
        },
        prepareNewView: function () {
            let {res_model} = this.action, {viewType} = this.state, viewInfo = {view_mode: viewType, action_id: this.action.id}, data = {};
            data.arch = QWeb.templates[`ViewEdit.${viewType.charAt(0).toUpperCase() + viewType.slice(1)}Default`].innerHTML;
            data.name = `${res_model}.${viewType}`;
            data.model = res_model;
            viewInfo.data = data;
            return viewInfo;
        },
        reloadProperty: function () {
            this.$el.find('._editProperty ._cCeP').empty().append(this.ref.view.ref.property.$el);
        },
        showSubView: function (node, viewInfo) {
            const {viewType} = this.state, subView = this.viewsInfo[viewType].subView;
            if (viewInfo.type in subView) {
                let View = new subView[viewInfo.type].widget(this, {viewInfo: viewInfo, _processFieldsView: this._processFieldsView,
                    action: this.action, editView: this, rootViewType: viewType,
                    nodeId: node.nodeId, parent_view_id: this.getViewInfo().view_id || false});
                this.ref.subView = View;
                this.ref.view.disableSort();
                this.$el.addClass("_showSubView");
                this.$el.find('._editView ._wSubView').addClass("show").append(View._renderContent());
                this.$el.find('._editProperty ._cCeP').empty().append(View._renderProperty());
            }
        },
        closeSubView: function (e) {
            e.stopPropagation();
            e.stopImmediatePropagation();
            const nodeId = this.ref.subView.nodeId, subViewType = this.ref.subView.viewInfo.type;
            $(e.currentTarget).empty().removeClass("show");
            this.$el.removeClass("_showSubView");
            delete this.ref.subView;
            this.ref.view.onCloseSubView(nodeId, subViewType);
            this.ref.view._renderProperty(true);
            this.ref.view.enableSort();
            if (nodeId) {
                this.ref.view.ref.content.reloadNode(nodeId);
            }
        },
        _switchView: function () {
            let self = this;
            const {viewType} = this.state;
            if (viewType in self.fieldsViews) {
                this.ref.view = new this.viewsInfo[viewType].widget(this,
                    {
                        editView: this,
                        action: this.action,
                        _processFieldsView: this._processFieldsView,
                        rootViewType: viewType,
                        reloadProperty: this.reloadProperty.bind(this),
                        viewInfo: this.getViewInfo(),
                        controller: this.controller,
                        showSubView: this.showSubView.bind(this)
                    });
                this.$el.find('._editView ._wMainView').empty().append(this.ref.view._renderContent());
                this.$el.find('._editProperty ._cCeP').empty().append(this.ref.view._renderProperty());
                this.$el.attr({'view-type': viewType});
            }else {
                this.createNewView().then(() => {
                    self.renderElement();
                });
            }
        },
        _renderMenu: function () {
            const {viewType} = this.state;
            let wrap = this.$el.find('._hEView'), wrapUl = $(QWeb.render("EditView.menu", {}))
            Object.keys(this.viewsInfo).map((type) => {
                let view = this.viewsInfo[type], item = $(QWeb.render("EditView.menuItem", {...view}));
                if (type == viewType) {
                    item.addClass("active");
                }
                item.click(() => {
                    wrapUl.find("li.active").removeClass("active");
                    item.addClass("active");
                    this.onClickView(type);
                });
                wrapUl.append(item);
            });
            wrap.append(wrapUl);
        },
        _renderView: function () {
            this._renderMenu();
            this._switchView();
            this.bindStyle();
            this.bindAction();
        },
        renderView: function () {
            let self = this;
            const state = $.bbq.getState(true);
            this.action_manager = new ActionManager(this, session.user_context);
            this.action_manager.isInDOM = true;
            this.action_manager.doAction = function (action, options) {
                let props = {
                    from_odo_studio: Math.random(),
                    active_id: options.additional_context.active_id,
                    active_ids: options.additional_context.active_ids,
                    active_model: options.additional_context.active_model,
                }
                return self.action_manager._loadAction(action, props).then(function (action) {
                    self.action_manager._preprocessAction(action, options);
                    return action;
                })
            };
            this.action_manager.loadState(state).then(function (action) {
                self.action = action;
                self.action_manager._loadViews(action).then((fieldsViews) => {
                    self.fieldsViews = fieldsViews;
                    self._renderView();
                });
            });
        },
        renderElement: function () {
            this._super();
            this.renderView();
        }
    });

    return EditView;
});
