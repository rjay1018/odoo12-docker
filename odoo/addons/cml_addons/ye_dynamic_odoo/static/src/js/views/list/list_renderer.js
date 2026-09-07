odoo.define('ye_dynamic_odoo.list_renderer', function(require) {

    var ListRenderer = require('web.ListRenderer');
    var relational_fields = require('web.relational_fields');
    var FieldMany2One = require('web.relational_fields').FieldMany2One;
    var Widget = require('web.Widget');
    var BasicModel = require('web.BasicModel');
    var widget = new Widget();
    var model = new BasicModel(widget);

    var ListController = require('web.ListController');
    // var QWeb = core.qweb;


    ListController.include({
        init: function (parent, model, renderer, params) {
            this._super(parent, model, renderer, params);
            if (parent.searchview) {
                parent.searchview.listViewRender = renderer;
            }
        }
    });

    ListRenderer.include({
        init: function (parent, state, params) {
            this._super(parent, state, params);
            this.viewInfo = params.viewInfo;
            this.search_domain = {};
            this.parent = parent;
            this.showSearchAdvance = false;
            this.showSticky = false;
            if (this.arch ) {
                let search_advance = this.arch.attrs.search_advance;
                let sticky = this.arch.attrs.sticky;
                this.showSearchAdvance = [true, "true", "1", 1, "True"].includes(search_advance) ? true : false;
                this.showSticky = [true, "true", "1", 1, "True"].includes(sticky) ? true : false;
            }
            this.fieldRender = {char: {render: this.renderFieldInput.bind(this)}, float: {render: this.renderFieldInput.bind(this)},
                                int: {render: this.renderFieldInput.bind(this)}, many2one: {render: this.renderFieldMany2one.bind(this)},
                                date: {render: this.renderFieldDate.bind(this)}, datetime: {render: this.renderFieldDate.bind(this)},
                                selection: {render: this.renderFieldSelection.bind(this)}
                }
        },
        on_attach_callback: function () {
            this._super();
            if (this.showSticky) {
                var $self = this;
                var o_content_area = $(".o_content")[0];

                function sticky() {
                    $self.$el.find("table.o_list_view").each(function () {
                        $(this).stickyTableHeaders({scrollableArea: o_content_area, fixedOffset: 0.1});
                    });
                }

                function fix_body(position) {
                    $("body").css({
                        'position': position,
                    });
                }

                if (this.$el.parents('.o_field_one2many').length === 0) {
                    sticky();
                    fix_body("fixed");
                    $(window).unbind('resize', sticky).bind('resize', sticky);
                    this.$el.css("overflow-x", "visible");
                }
                else {
                    fix_body("relative");
                }
                $("div[class='o_sub_menu']").css("z-index", 4);
            }
        },
        renderFieldMany2one: function (field, container) {
            let self = this;
            const {name} = field;
            var many2one = new FieldMany2One(self, name, this.state, {
                mode: 'edit',
                viewType: this.viewType,
            });
            many2one.appendTo(container);
            const _setValue = function (value, options) {
                if (this.lastSetValue === value || (this.value === false && value === '')) {
                    return $.when();
                }
                this.lastSetValue = value;
                value = this._parseValue(value);
                this.$input.val(value.display_name);
                value ? (self.search_domain[name] = value.display_name) : (delete self.search_domain[name]);
                self._searchRenderData();
                var def = $.Deferred();
                return def;
            }
            many2one.$input.val(this.search_domain[name] || null);
            many2one._setValue = _setValue.bind(many2one);
        },
        renderFieldInput: function (field, container) {
            let self = this, view = $('<input>'), {name} = field;
            view.keyup(function (e) {
                let val = view.val();
                val ? (self.search_domain[name] = val) : (delete self.search_domain[name]);
                if (e.keyCode == 13) {
                    self._searchRenderData();
                }
            });
            view.val(this.search_domain[name] || null);
            container.append(view);
        },
        renderFieldDate: function (field, container) {
            let self = this, {name} = field, view = $('<input name='+name+'>'), format = "DD/MM/YYYY",
                options = {autoUpdateInput: false, locale: {cancelLabel: 'Clear', format: format}};
            view.daterangepicker(options);
            view.change((ev) => {
                let value = ev.target.value;
                if (!value) {
                    delete self.search_domain[name];
                    self._searchRenderData();
                }
            });
            view.on('apply.daterangepicker', (ev, picker) => {
                const {startDate, endDate} = picker, val = startDate.format(format) + ' - ' + endDate.format(format);
                val ? (self.search_domain[name] = val) : (delete self.search_domain[name]);
                self._searchRenderData();
            });
            view.on('cancel.daterangepicker', () => {
                delete self.search_domain[name];
                self._searchRenderData();
            });
            view.val(this.search_domain[name] || null);
            container.append(view);
        },
        renderFieldSelection: function (field, container) {
            let self = this, {name} = field,
                view = $('<select><option></option></select>');
            field.selection.map((option) => {
                const [value, name] = option;
                view.append($('<option value='+value+'>'+name+'</option>'));
            });
            view.change(function () {
                let val = view.val();
                val ? (self.search_domain[name] = val) : (delete self.search_domain[name]);
                self._searchRenderData();
            });
            view.val(this.search_domain[name] || null);
            container.append(view);
        },
        _renderHeader: function (isGrouped) {
            let res = this._super(isGrouped);
            if (this.showSearchAdvance) {
                let $tr = $('<tr class="_trSearch">').append(_.map(this.columns, this._renderSearch.bind(this)));
                if (this.hasSelectors) {
                    $tr.prepend($('<th>'));
                }
                res.append($tr);
            }
            return res;
        },
        _prepareSearchDomains: function () {
            let result = [], fields = this.state.fields;
            Object.keys(this.search_domain).map((d, idx) =>{
                let field = fields[d], val = this.search_domain[d];
                if (field.type == 'datetime'){
                    val = val.split(" - ");
                    let formatClient = "DD/MM/YYYY", formatServer = "YYYY/MM/DD",
                        from = (moment(val[0], formatClient)).format(formatServer),
                        to = (moment(val[1] || val[0], formatClient)).format(formatServer);
                    result.push([d, '>=', `${from}_00:00:00`]);
                    result.push([d, '<=', `${to}_23:59:59`]);
                }else if (field.type == 'date') {
                    val = val.split(" - ");
                    let formatClient = "DD/MM/YYYY", formatServer = "YYYY/MM/DD",
                        from = (moment(val[0], formatClient)).format(formatServer),
                        to = (moment(val[1] || val[0], formatClient)).format(formatServer);
                    result.push([d, '>=', from]);
                    result.push([d, '<=', to]);
                }else if (['int', 'float'].indexOf(field.type) >= 0) {
                    result.push([d, '=', parseFloat(val)]);
                }else {
                    result.push([d, 'ilike', val]);
                }
            });
            return result
        },
        _searchRenderData: function () {
            var searchView = this.parent.searchview;
            var search = searchView.build_search_data();
            searchView.trigger_up('search', search);
        },
        _renderSearch: function (node) {
            let name = node.attrs.name, $th = $('<th>'),
                field = {...this.state.fields[name], name: name};
            if (!field || !(field.type in this.fieldRender)) {
                return $th;
            }
            this.fieldRender[field.type].render(field, $th)
            return $th;
        },
        _hasContent: function () {
            let result = this._super();
            if (Object.keys(this.search_domain).length > 0) {
                return true;
            }
            return result;
        },

    });

});
