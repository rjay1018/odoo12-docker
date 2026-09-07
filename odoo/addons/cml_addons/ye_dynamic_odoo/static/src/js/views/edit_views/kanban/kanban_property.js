odoo.define('ye_dynamic_odoo.KanbanViewProperty', function (require) {
"use strict";

    var core = require('web.core');
    var Base = require('ye_dynamic_odoo.BaseEdit');
    var FieldBasic = require('ye_dynamic_odoo.FieldBasic');
    var QWeb = core.qweb;


    var KanbanViewProperty = Base.PropertyBase.extend({
        start: function () {
            this._super();
            const {property, view} = this.property;
            view.kanban = {};
            view.kanban.kanban = [];
            this.setState({tab: "property"});
            delete this.tabs.component;
            delete this.tabs.fields;
            property.name = {label: "Field", widget: FieldBasic.Selection};
            // this.tabs.template = {label: "Template", name: "template", icon: "fa-foursquare", render: this._renderTabTemplate.bind(this)};
            // this.templates = {template1: {label: "Template Default", name: "template1", template: "KanBan.Template1", img: "/ye_dynamic_odoo/static/src/img/template1.png"},
            //     template2: {label: "Template 2", name: "template2", template: "KanBan.Template2", img: "/ye_dynamic_odoo/static/src/img/template2.png"}};
            view.kanban.field = ["invisible", "string", "widget"];
            view.kanban.kanban = ["create", "quick_create"];
            this.preparePropertyInfo();
        },
        preparePropertyInfo: function () {
            const {viewInfo} = this.props, data = {name: []}, {fieldsGet} = viewInfo;
            for (let [key, value] of Object.entries(fieldsGet)) {
                let item = {label: value.string, value: key};
                data.name.push(item)
            }
            Object.keys(data).map((propName) => {
                this.property.property[propName].props = {data: data[propName]}
            });
            return data;
        },
        bindAction: function () {
            this._super();
            this.$el.find(".templateItem").click(this.onClickTemplate.bind(this));
        },
        onClickAddTag: function (tagType, addId) {
            const {viewInfo} = this.props, {fieldsGet} = viewInfo, data = [];
            for (let [key, value] of Object.entries(fieldsGet)) {
                let option = {label: value.string, value: key}
                if (tagType == "tags") {
                    if (value.type == "many2many") {
                        data.push(option);
                    }
                }else if (tagType == "img") {
                    if (value.type == "many2one" && value.relation == "res.users") {
                        data.push(option);
                    }
                }else if (tagType == "color") {
                    if (value.type == "integer") {
                        data.push(option);
                    }
                }else if (tagType == "activity") {
                    if (key == "activity_ids") {
                        data.push(option);
                    }
                }else if (tagType == "priority") {
                    if (value.type == "selection") {
                        data.push(option);
                    }
                }else{
                    data.push(option);
                }
            }
            this.curAddId = addId;
            let fieldSelect = new FieldBasic.Selection(this, {label: "Select Field", data: data,
                onChange: this.onChangeFieldSelect.bind(this)});
            fieldSelect.renderElement();
            this.$el.find(".wLProP").empty().append(fieldSelect.$el);
            // this.$el.find(".wLProP").empty().append(this._renderProperty(node));
        },
        onChangeFieldSelect: function (fieldName) {
            const {onChangeFieldSelect} = this.props;
            onChangeFieldSelect(fieldName, this.curAddId);
        },
        onClickTab: function () {
            this._super();
            this.bindAction();
        },
        onClickTemplate: function (e) {
            e.stopPropagation();
            const el = $(e.currentTarget), templateName = el.attr("template"), template = this.templates[templateName], {onChangeTemplate} = this.props;
            if (template && onChangeTemplate) {
                onChangeTemplate(QWeb.templates[template.template].innerHTML);
            }
        },
        _renderTabTemplate: function () {
            return $(QWeb.render("KanBanViewEdit.Tab.Theme", {templates: this.templates}));
        }
    });

    return KanbanViewProperty;
});
