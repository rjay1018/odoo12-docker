odoo.define('ye_dynamic_odoo.FieldBasic', function (require) {
"use strict";

    var core = require('web.core');

    var QWeb = core.qweb;
    var Widget = require('web.Widget');
    var BasicField = require('web.basic_fields');
    var FieldRegistry = require('web.field_registry')

    var Radio = Widget.extend({
        template: 'EditView.Radio',
        init: function(parent, params) {
            const {value} = params;
            this.props = params;
            this.state = {value: value || false};
        },
        setState: function (params) {
            Object.keys(params).map((name) => {
                this.state[name] = params[name];
            });
        },
        _onCheck: function (e) {
            const {value} = this.state, {onCheck} = this.props;
            this.setState({value: !value});
            this.bindClass();
            if (!value && onCheck) {
                onCheck(this.props);
            }
        },
        getValue: function () {
            return this.state.value;
        },
        setValue: function (value) {
            this.setState({value: value});
        },
        bindAction: function () {
            this.$el.click(this._onCheck.bind(this));
        },
        bindClass: function () {
            const {value} = this.state;
            value ? this.$el.addClass("checked") : this.$el.removeClass("checked");
        },
        reload: function () {
            this.renderElement();
        },
        renderElement: function () {
            this._super();
            this.bindClass();
            this.bindAction();
        }
    });

    var Checkbox = Widget.extend({
        template: 'EditView.Checkbox',
        init: function(parent, params) {
            const {value} = params;
            this.props = params;
            this.readonly = params.readonly || false;
            this.state = {value: this.prepareValue(value)};
        },
        setState: function (params) {
            Object.keys(params).map((name) => {
                this.state[name] = params[name];
            });
        },
        prepareValue: function (value) {
            return ["1", "True", "true", true].includes(value);
        },
        _onCheck: function (e) {
            if (!this.readonly) {
                let el = $(e.currentTarget);
                const {value} = this.state, {onChange} = this.props;
                value ? el.removeClass("checked") : el.addClass("checked");
                this.setState({value: !value});
                if (onChange) {
                    onChange(!value);
                }
            }
        },
        getValue: function () {
            return this.state.value;
        },
        setValue: function (value) {
            this.setState({value: value});
        },
        bindAction: function () {
            this.$el.click(this._onCheck.bind(this));
        },
        bindClass: function () {
            const {value} = this.state, {noLabel} = this.props;
            value ? this.$el.addClass("checked") : this.$el.removeClass("checked");
            if (noLabel) {
                this.$el.find(".lblField").addClass("hide");
            }
        },
        reload: function () {
            this.renderElement();
        },
        renderElement: function () {
            this._super();
            this.bindClass();
            this.bindAction();
        }
    });

    var GroupRadio = Widget.extend({
        template: 'EditView.Radio.Group',
        init: function(parent, params) {
            this.props = params;
            this.ref = {checks: []};
        },
        _renderRadio: function () {
            const {selection} = this.props, wRadio = this.$el.find("._wGrCc");
            selection.map((item) => {
                let radio = new Radio(this, {...item, onCheck: this.onCheck.bind(this)});
                this.ref.checks.push(radio);
                radio.renderElement();
                wRadio.append(radio.$el);
            });
        },
        onCheck: function (data) {
            this.ref.checks.filter((radio) => radio.props.key !== data.key).map(
                (radio) => {
                    radio.setState({value: false});
                    radio.bindClass();
                });
        },
        bindStyle: function () {
            const {noLabel, direction} = this.props;
            if (noLabel) {
                this.$el.find("._wGrHead.lblField").addClass("hide");
            }
            this.$el.addClass(direction || "_column");
        },
        renderElement: function () {
            this._super();
            this._renderRadio();
            this.bindStyle();
        }
    });

    var GroupCheckBox = Widget.extend({
        template: 'EditView.Checkbox.Group',
        init: function(parent, params) {
            this.props = params;
            this.ref = {checks: []};
        },
        _renderRadio: function () {
            const {selection} = this.props, wCheckbox = this.$el.find("._wGrCc");
            selection.map((item) => {
                let checkbox = new Checkbox(this, {...item});
                this.ref.checks.push(checkbox);
                checkbox.renderElement();
                wCheckbox.append(checkbox.$el);
            });
        },
        onCheck: function (data) {},
        bindStyle: function () {
            const {noLabel} = this.props;
            if (noLabel) {
                this.$el.find("._wGrHead.lblField").addClass("hide");
            }
        },
        renderElement: function () {
            this._super();
            this._renderRadio();
            this.bindStyle();
        }
    });

    var Input = Widget.extend({
        template: 'EditView.Input',
        init: function (parent, params) {
            const {value} = params;
            this.props = params;
            this.modifiers = params.modifiers || {};
            this.oldVal = value;
            this.state = {value: value || ""};
            this.ref = {};
        },
        setState: function (params) {
            Object.keys(params).map((name) => {
                this.state[name] = params[name];
            });
        },
        setValue: function (value) {
            this.setState({value: value || ""});
        },
        getValue: function () {
            return this.state.value;
        },
        onKeyUp: function (e) {
            const {onChange} = this.props, value = $(e.currentTarget).val();
            this.setState({value: value});
            if (onChange && e.keyCode == 13) {
                this.oldVal = value;
                onChange(value);
            }
            this.$el[this.oldVal != value ? "addClass" : "removeClass"]("_oSave");
        },
        bindAction: function () {
            this.$el.find("input").keyup(this.onKeyUp.bind(this));
        },
        bindStyle: function () {
            const {readonly, required, noLabel} = this.props;
            if (this.modifiers.required || required) {
                this.$el.addClass("required");
            }
            if (this.modifiers.readonly || readonly) {
                this.$el.find("input,textarea").addClass("readonly");
            }
            if (this.modifiers.nolabel || noLabel) {
                this.$el.find(".lblField").addClass("hide");
            }
            // if (readonly) {
            //     this.$el.find("input,textarea").attr({readonly: "readonly"});
            // }
        },
        reload: function () {
            this.renderElement();
        },
        renderElement: function () {
            this._super();
            this.bindAction();
            this.bindStyle();
        }
    });

    var WidgetBase = Widget.extend({
        init: function (parent, params) {
            // this._super(parent);
            this.ref = {};
            this.props = params;
            this.start();
        },
        start: function () {},
        setState: function (params) {
            Object.keys(params).map((name) => {
                this.state[name] = params[name];
            });
        },
        _beforeRender: function () {

        },

        _afterRender: function () {

        },
        bindAction: function () {

        },
        reload: function () {
            this.renderElement();
        },
        renderElement: function () {
            this._beforeRender();
            this._super();
            this.bindAction();
            this._afterRender();
        }
    });

    var One2many = WidgetBase.extend({

    });



    var Tab = WidgetBase.extend({
        template: 'ViewEdit.Tab',
        init: function (parent, params) {
            this._super(parent, params);
            this.newTab = {};
            this.state = {data: params.data};
            this.ref = {};
        },
        bindClass: function () {
            const {data} = this.state;
            this.$el.find("> ._tabHead > [tab-name]").removeClass("active");
            this.$el.find("[tab-name='"+data+"']").addClass("active");
        },
        binAction: function () {
            this.$el.find('> ._tabHead > [tab-name]').click(this.onClickTab.bind(this));
        },
        onAddTab: function () {
            const {onAddTab, fieldNode} = this.props;
            onAddTab(fieldNode.nodeId)
        },
        onClickTab: function (e) {
            // e.stopPropagation();
            // e.stopImmediatePropagation();
            const {add, onClickTab} = this.props;
            let $el = $(e.currentTarget), tabName = $el.attr("tab-name");
            if (tabName === 'add' && add) {
               this.onAddTab();
               return true;
            }
            this.setState({data: tabName});
            this._renderTabContent();
            if (onClickTab) {
                onClickTab();
            }
        },
        _renderTabContent: function (force=false) {
            const {data} = this.state;
            this.$el.find("[content-for]").removeClass("show").addClass("hide");
            if (!(data in this.ref) || force) {
                this.ref[data] = this.tabs[data].render();
                this.ref[data].attr({"content-for": data});
                this.$el.find('[content-for="'+data+'"]').remove();
                this.$el.find('._tabContent').append(this.ref[data]);
            }else {
                let tabContent = this.$el.find("[content-for='"+data+"']");
                if (!tabContent.length) {
                    this.$el.find('._tabContent').append(this.ref[data]);
                }
                this.$el.find("[content-for='"+data+"']").removeClass("hide").addClass("show");
            }
            this.bindClass();
        },
        _beforeRender: function () {
            const {add, tabs} = this.props;
            this.tabs = Object.assign(tabs || {}, this.newTab);
            delete this.tabs["add"];
            if (add) {
                this.tabs['add'] = {icon: "fa fa-plus", name: "add"};
            }
        },
        reload: function () {
            this._super();
        },
        renderElement: function () {
            this._super();
            this._renderTabContent();
            this.binAction();
        }
    });

    var Button = Widget.extend({
        template: 'ViewEdit.Button',
        init: function (parent, params) {
            this.state = {type: "action"}
        },
        onClickBtn: function () {
            alert("ok");
        },
        binAction: function () {
            this.$el.click(this.onClickBtn.bind(this));
        },
        renderElement: function () {
            this._super();
            this.binAction();
        }
    });

    var TextArea = Input.extend({
        template: 'EditView.TextArea',
    });

    var Many2manyTagCheckbox = GroupCheckBox.extend({
        init: function(parent, params) {
            const {record, name} = params;
            let selection = record.specialData[name].map((option) => ({value: option[0], label: option[1]}));
            params.selection = selection;
            this._super(parent, params);
        }
    });

    var RadioWidget = GroupRadio.extend({
        init: function(parent, params) {
            const {record, field, name, fieldsInfo} = params;
            // let val = field.selection ? field.selection.filter((option) => option[0] == record.data[name]) : [];
            // this.nodeOptions.horizontal ? ' o_horizontal' : ' o_vertical';
            let selection = field.selection.map((option) => ({value: option[0], label: option[1]}));
            params.selection = selection;
            params.direction = (fieldsInfo.options || {}).horizontal ? "_row" : "_column";
            this._super(parent, params);
        }
    });

    var Char = Input.extend({
        init: function(parent, params) {
            const {record, name} = params;
            params.value = record.data[name];
            this._super(parent, params);
        }
    });

    var Integer = Input.extend({
        init: function(parent, params) {
            const {record, name} = params;
            params.value = String(record.data[name]);
            this._super(parent, params);
        }
    });

    var Many2one = Input.extend({
        init: function(parent, params) {
            const {record, name} = params, data = record.data[name];
            params.value = data ? data.data.display_name || "" : "";
            this._super(parent, params);
        }
    });

    var Selection = WidgetBase.extend({
        template: "Edit.Field.Selection",
        init: function (parent, params) {
            this._super(parent, params);
            this.state = {value: params.value || false}
        },
        start: function () {
            this.data = this.prepareData();
        },
        getValue: function () {
            return this.state.value;
        },
        prepareData: function () {
            const {data} = this.props;
            return data;
            // const {fieldType} = this.props;
            // return Object.keys(FieldRegistry.map).filter((widgetName) => {
            //     let widget = FieldRegistry.map[widgetName], {supportedFieldTypes} = widget.prototype;
            //     return supportedFieldTypes && supportedFieldTypes.includes(fieldType || "char");
            // }).map((widgetName) => ({label: this.capitalize(widgetName), value: widgetName}));
        },
        onChangeValue: function (e) {
            const {onChange} = this.props;
            let value = $(e.currentTarget).val();
            this.setState({value: value});
            if (onChange) {
                onChange(value);
            }
        },
        bindAction: function () {
            this.$el.find("select").change(this.onChangeValue.bind(this));
            this.$el.find("select").val(this.getValue());
        }
    });


    var Condition = WidgetBase.extend({
        template: "Edit.Field.Condition",
        init: function (parent, params) {
            this._super(parent, params);
        },
        _renderEditUI: function () {

        },
        _renderCodeEdit: function () {
            const {value} = this.props;
            this.inputEdit = new Input(this, {...this.props, label: "# Code editor  (enter to save)", value: value || "[]"});
            this.inputEdit.renderElement();
            this.$el.find("._ecCodeEdit").append(this.inputEdit.$el);
        },
        renderElement: function () {
            this._super();
            this._renderEditUI();
            this._renderCodeEdit();
        }
    });

    var CBCondition = WidgetBase.extend({
        template: "Edit.Field.CBCondition",
        init: function (parent, params) {
            this._super(parent, params);
            this.state = {show: false, value: params.value || false}
        },
        toggleCondition: function (e) {
            e.stopPropagation();
            const {show} = this.state;
            this.setState({show: !show});
            this.$el.find("._editCondition")[!show ? "addClass" : "removeClass"]("show");
        },
        getData: function () {
            const {value} = this.state;
            return this.checkValue(value) ? value : this.ref.checkbox.getValue();
        },
        checkValue: function (value) {
            let isCondition = (typeof value == "string" && value != "[]" && value.length) || (Array.isArray(value) && value.length);
            return isCondition;
        },
        onChangeValue: function (value) {
            const {onChange} = this.props;
            this.setState({value: value});
            this.bindStyle();
            if (onChange) {
                onChange(this.getData());
            }
        },
        onKeyUp: function (value) {
            this.setState({value: value});
            this.bindStyle();
        },
        bindStyle: function () {
            const {value} = this.state;
            let isCondition = this.checkValue(value);
            this.ref.checkbox.$el[isCondition ? "addClass" : "removeClass"]("_useCondition");
            this.ref.checkbox.readonly = isCondition;
        },
        bindAction: function () {
            this.$el.find("._wCbCon > span").click(this.toggleCondition.bind(this));
        },
        renderView: function () {
            const {value} = this.state;
            this.ref.condition = new Condition(this, {...this.props, onChange: this.onChangeValue.bind(this),
                value: Array.isArray(value) ? JSON.stringify(value) : "[]"});
            this.ref.checkbox = new Checkbox(this, {...this.props, value: value, onChange: this.onChangeValue.bind(this)});
            this.ref.condition.renderElement();
            this.ref.checkbox.renderElement();
            this.$el.find("._wCbCon").append(this.ref.checkbox.$el).append("<span>Condition</span>");
            this.$el.find("._wEditCon").append(this.ref.condition.$el);
        },
        renderElement: function () {
            this._super();
            this.renderView();
            this.bindStyle();
            this.bindAction();
        }
    });

    var WidgetOption = WidgetBase.extend({
        template: "Edit.Field.Widget",
        init: function (parent, params) {
            this._super(parent, params);
            this.state = {value: params.value || false}
        },
        start: function () {
            this.fieldsWidget = this.prepareData();
        },
        getValue: function () {
            return this.state.value;
        },
        capitalize: function (name) {
            return name.split("_").map((str) => str.charAt(0).toUpperCase() + str.slice(1)).join(" ");
        },
        prepareData: function () {
            const {fieldType} = this.props;
            return Object.keys(FieldRegistry.map).filter((widgetName) => {
                let widget = FieldRegistry.map[widgetName], {supportedFieldTypes} = widget.prototype;
                return !["report_layout"].includes(widgetName) && supportedFieldTypes && supportedFieldTypes.includes(fieldType || "char");
            }).map((widgetName) => ({label: this.capitalize(widgetName), value: widgetName}));
        },
        onChangeValue: function (e) {
            const {onChange} = this.props;
            let value = $(e.currentTarget).val();
            this.setState({value: value});
            if (onChange) {
                onChange(value);
            }
        },
        bindAction: function () {
            this.$el.find("select").change(this.onChangeValue.bind(this));
            this.$el.find("select").val(this.getValue());
        }
    });

    var ColorLine = Widget.extend({
        template: "ViewEdit.ColorLine",
        init: function (parent, params) {
            const {value} = params;
            this.props = params;
            this.oldVal = value || {};
            this.state = {value: value || {}};
            this.viewInfo = {danger: {}, warning: {}, success: {}, primary: {}, info: {}, muted: {}, bf:
                    {placeholder: "Bold"}, it: {placeholder: "Italic"}};
        },
        setState: function (params) {
            Object.keys(params).map((name) => {
                this.state[name] = params[name];
            });
        },
        getValue: function () {
            return this.state.value;
        },
        setValue: function (value) {
            this.setState({value: value});
        },
        onKeyUp: function (e) {
            let self = this;
            const {onChange} = this.props, {value} = this.state;
            let el = $(e.currentTarget), name = el.attr("name"), newVal = {...value, [name]: el.val()} ;
            this.setState({value: newVal});
            if (onChange && e.keyCode == 13) {
                this.oldVal = newVal;
                onChange(newVal);
            }
            Object.keys(newVal).map((colorName) => {
                let oldVal = self.oldVal[colorName];
                self.$el.find("div[name='"+colorName+"']")[oldVal != newVal[colorName] ? "addClass" : "removeClass"]("_oSave");
            });
        },
        bindAction: function () {
            this.$el.find('._lColor input').keyup(this.onKeyUp.bind(this));
        },
        reload: function () {
            this.renderElement();
        },
        renderElement: function () {
            this._super();
            this.bindAction();
        }
    });

    return {ColorLine: ColorLine, WidgetOption: WidgetOption, CBCondition: CBCondition, Condition: Condition,
        RadioWidget: RadioWidget, Char: Char, Integer: Integer, Many2one: Many2one, Selection: Selection,
        Many2manyTagCheckbox: Many2manyTagCheckbox, Radio: Radio, Checkbox: Checkbox, GroupRadio: GroupRadio,
        GroupCheckBox: GroupCheckBox, Input: Input, Tab: Tab, Button: Button, TextArea: TextArea}
});
