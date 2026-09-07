odoo.define('ye_dynamic_odoo.menu', function (require) {
"use strict";

    var core = require('web.core');
    var Menu = require('web.Menu');
    var view_dialogs = require('web.view_dialogs');
    var FormViewDialog = view_dialogs.FormViewDialog;
    var QWeb = core.qweb;

    Menu.include({
        init: function (parent, menu_data) {
            this._super(parent, menu_data);
            this.menuObj = {};
            this.menudeleted = [];
            this.events['click ._liEdit'] = '_onClickMenuEdit';
            this.events['click ._btnConfirm'] = 'getDataEdit';
            this.events['click ._aClose'] = '_onClickClose';
            this.events['click ._wAdd'] = '_onClickAdd';
            this.events['click ._wEdit'] = '_onClickEdit';
            this.events['click ._wRemove'] = '_onRemove';
            this.events['keyup ._wName input'] = '_onKeyPressName';
        },
        _onRemove: function (e) {
            let $line = $(e.currentTarget).closest('li'),
                lineId = $line.attr("view-data");
            if (!String(lineId).includes("new")) {
                $line.find('._liSub').map((idx, el) => this.menudeleted.push(+$(el).attr("view-data")));
                this.menudeleted.push(+lineId);
            }
            $line.remove();
        },
        setAttrObj: function (_id, params) {
            if (_id && _id in this.menuObj) {
                let menu = this.menuObj[_id];
                Object.keys(params).map((attr) => {
                    menu[attr] = params[attr]
                });
            }
        },
        _onKeyPressName: function (e) {
            let $el = $(e.currentTarget);
            if (e.keyCode == 13) {
                $el.removeClass("_show");
                $el.prev().removeClass("_hide");
                this.setAttrObj($el.closest('li').attr("view-data"), {name: $el.val()});
            }else {
                $el.prev().text($el.val());
            }
        },
        _onClickAdd: function (e) {
            let self = this, $line = $(e.currentTarget).parent().parent(), lineId = $line.attr("view-data"),
                lineData = this.menuObj[lineId], {sequence, parent_id, id} = lineData,
                newData = {...lineData, name: "New Menu", id: 'new'+String(moment().valueOf()), sequence: sequence+1, type: "new"},
                lineRelate = parent_id ? Object.values(this.menuObj).filter(
                    (menu) => menu.parent_id && menu.id != id && (menu.parent_id[0] == parent_id[0])
                        && menu.sequence >= sequence) : [], listSeq = [sequence, newData.sequence];
            lineRelate.map((menu) => {
                const {sequence} = menu;
                menu.sequence = this._checkSequence(sequence, listSeq);
                listSeq.push(menu.sequence);
            });
            let context = {
                default_parent_id: parent_id ? +parent_id[0] : false,
                default_sequence: newData.sequence
            }
            this._rpc({
                model: "ir.ui.menu",
                method: 'get_form_view_id',
                args: ["create"],
            }).then(function (viewId) {
                self.onShowFormDialog(false, viewId, "Create Menu",
                    (record) => {},
                    () => {}, context);
            });
        },
        _onClickEdit: function (e) {
            let self = this;
            this._rpc({
                model: "ir.ui.menu",
                method: 'get_form_view_id',
                args: ["edit"],
            }).then(function (viewId) {
                self.onShowFormDialog(+$(e.currentTarget).closest('li').attr("view-data"), viewId, "Edit Menu");
            });
        },
        onShowFormDialog: function (res_id, viewId, title, save = (record) => {}, remove = () => {}, context={}) {
            let self = this;
            let dialog = null, options = {
                res_model: "ir.ui.menu", res_id: res_id,
                context: context, title: title, view_id: viewId,
                disable_multiple_selection: true, size: "small", deletable: true,
                on_saved: (record) => {
                    save(record);
                    self.reload_menu();
                },
                on_remove: () => {
                    remove(res_id);
                }
            };
            dialog = new FormViewDialog(this, options);
            dialog.open()
        },
        _onClickClose: function () {
            this.$el.find('._bgEdit').remove();
        },
        change_menu_section: function (primary_menu_id) {
            this._super(primary_menu_id);
            this.$el.find("._menuEdit").remove();
            this.$edit = $(QWeb.render('menu.edit', {widget: this}));
            this.$section_placeholder.find('li:last-child').after(this.$edit);
        },
        _renderLineEdit: function (menu) {
            const {children, id} = menu;
            this.menuObj[id] = menu;
            let wrapLine = $(QWeb.render("MenuEdit.li", menu));
            if (children && children.length) {
                wrapLine.append(this._renderMenuEdit(children));
            }
            return wrapLine
        },
        _renderMenuEdit: function (menus){
            let wrapUlEdit = $('<ul class="_wrapUlEdit">');
            menus.map((menu) => {
                wrapUlEdit.append(this._renderLineEdit(menu));
            });
            return wrapUlEdit;
        },
        _checkSequence: function (sequence, listSeq) {
            if (!listSeq.includes(sequence)) {
                return sequence;
            }
            sequence += 1;
            if (sequence in listSeq) {
                return this._checkSequence(sequence, listSeq)
            }
            return sequence;
        },
        onStopSort: function ($item) {
            let _parentLi = $item.parent().parent(), parentId = _parentLi.attr("view-data"),
                lineObj = this.menuObj[$item.attr("view-data")], lineData = [];
            lineObj.parent_id = [+parentId, _parentLi.find(">._wInfo ._wName input").val()];
            $item.parent().find('>li').map((idx, line) => {
                lineData.push(this.menuObj[$(line).attr("view-data")]);
            });
            let sequences = lineData.map((child) => child.sequence).sort(), listSeq = [];
            lineData.map((child, idx) => {
                child.sequence = this._checkSequence(sequences[idx], listSeq);
                listSeq.push(child.sequence);
            });
        },
        _getLiParent: function (wrapCheck, heightCheck) {
            let liWrap = null, topCheck = 0;
            wrapCheck.find('li').map((idx, el) => {
                let $el = $(el), {top} = $el.position();
                if (top < heightCheck) {
                    if (!topCheck || top > topCheck) {
                        liWrap = $el;
                        topCheck = top;
                    }
                }
            });
            return liWrap
        },
        _getLiWrap: function (wrapCheck, heightCheck) {
            let $item = wrapCheck.find('li');
            if (!$item.length) {
                return wrapCheck;
            }
            let liWrap = this._getLiParent(wrapCheck, heightCheck), _wrapReal = liWrap.find('.ul');
            if (!_wrapReal.length) {
                _wrapReal = $('<ul class="_wrapUlEdit">');
                liWrap.append(_wrapReal);
            }
            return _wrapReal;
        },
        _getWrapMinHeight: function (ulWrap) {
            let _wrapReal = null, height = 0;
            ulWrap.map((idx, el) => {
                let $el = $(el), _height = $el.height();
                if (!height || _height < height) {
                    height = _height;
                    _wrapReal = $el;
                }
            });
            return _wrapReal;
        },
        _getUlPosition: function (wrap, heightCheck, leftCheck) {
            let ulWrap = wrap.find('._wrapUlEdit').filter((idx, el) => {
                let $el = $(el), {top} = $el.position();
                return (top + 30 + $el.height() > heightCheck);
            });
            // with li have not ul child.
            if (!ulWrap.length) {
                ulWrap = $('<ul class="_wrapUlEdit">');
                wrap.append(ulWrap);
                return ulWrap;
            }
            let _ulWrap = ulWrap.filter((idx, el) => {
                let $el = $(el), {left} = $el.position(), _left = leftCheck - 30;
                return (_left > left && _left < left+15);
            });
            if (!_ulWrap.length) {
                return this._getLiWrap(this._getWrapMinHeight(ulWrap), heightCheck);
            }
            ulWrap = _ulWrap;
            let _wrapReal = this._getWrapMinHeight(ulWrap);
            let level = Math.floor((leftCheck - 30 - _wrapReal.position().left)/30);
            if (level && _wrapReal.find('li').length) {
                _wrapReal = this._getLiWrap(_wrapReal, heightCheck);
            }
            return _wrapReal;
        },
        _onClickMenuEdit: function (e) {
            let self = this, $el = $(e.currentTarget);
            if (!$el.hasClass("render")) {
                let currentMenu = Object.values(this.menu_data.children).filter(
                    (menu) => menu.id == this.current_primary_menu),
                    wrapMenuEdit = $(QWeb.render("menu.ulEdit", {widget: this}));
                wrapMenuEdit.find('._con').append(this._renderMenuEdit(currentMenu));

                let params = {
                    connectWith: "._wrapUlEdit",
                    stop: function (evt, ui) {
                        let $item = ui.item, _top = $item.attr("top"), _left = $item.attr("left"),
                            leftType = ui.item.attr("leftType"), level = ui.item.attr("level");
                        $item.removeAttr("leftType");
                        if (leftType == "child") {
                            $item = ui.item.clone();
                            self._getUlPosition(ui.item.prev(), +_top, +_left).append($item);
                            wrapMenuEdit.find('._wrapUlEdit').sortable(params);
                            ui.item.remove();
                        }else if (leftType == "parent") {
                            if (+level != 0) {
                                $item = ui.item.clone();
                                let wrapUl = $(ui.item.parents('._liSub')[+level / -1]).find('>._wrapUlEdit');
                                let liWrap = null, topCheck = 0;
                                wrapUl.find('>li').map((idx, el) => {
                                    let $el = $(el), {top} = $el.position();
                                    if ((top + 30) < +_top) {
                                        if (!topCheck || (top + 30) > topCheck) {
                                            liWrap = $el;
                                        }
                                    }
                                });
                                if (liWrap) {
                                    liWrap.after($item);
                                    ui.item.remove();
                                }
                                wrapMenuEdit.find('._wrapUlEdit').sortable(params);
                            }
                        }
                        self.onStopSort($item);
                    },
                    sort: function ( event, ui ) {
                        const {left, top} = ui.position, leftChange = ui.helper.position().left - ui.originalPosition.left;
                        let prev = ui.helper.prev(), leftType = null, level = Math.round((leftChange)/30);

                        if (prev.length && leftChange > 30) {
                            leftType = "child";
                            let _ulChild = prev.find('ul:has(>li)');
                            if (!_ulChild.length) {
                                level = 1;
                            }else if (_ulChild.length && !_ulChild[level-1]) {
                                level = _ulChild.length+1;
                            }
                        } else if (leftChange < 0) {
                            leftType = "parent";
                        } else {
                            $(ui.item).removeAttr("leftType");
                            ui.placeholder.css({marginLeft: '0px'});
                        }
                        if (leftType) {
                            ui.placeholder.css({marginLeft: (level*30)+'px'});
                            $(ui.item).attr({leftType: leftType, level: level, top: top, left: left});
                        }
                    },
                    over: function (evt, ui) {
                        $(ui.placeholder).css({border: '1px dashed #dee2e6', visibility: 'inherit', marginBottom: '5px'});
                    }
                }
                wrapMenuEdit.find('._wrapUlEdit').sortable(params);
                this.$el.append(wrapMenuEdit);
                $el.attr({render: true});
            }
        },
        reload_menu: function () {
            let self = this;
            self.getParent().instanciate_menu_widgets().then(() => {
                core.bus.trigger('change_menu_section', self.current_primary_menu)
            });
        },
        getDataEdit: function () {
            let self = this, data = {...this.menuObj},
                result = {_newAll: [], _new: [], _parent: [], _old: [], _delete: this.menudeleted};
            this.menudeleted.map((menuId) => {
                if (menuId in data) {
                    delete data[menuId];
                }
            });
            Object.values(data).map((menu) => {
                const {type, parent_id} = menu;
                if (!parent_id || !(parent_id[0] in this.menudeleted)) {
                    if (parent_id && type == 'new') {
                        String(parent_id[0]).includes("new") ? result._newAll.push(menu) : result._new.push(menu);
                    } else {
                        String(parent_id[0]).includes("new") ? result._parent.push(menu) : result._old.push(menu);
                    }
                }
            })
            this._rpc({
                model: 'ir.ui.menu',
                method: 'update_menu',
                args: [result],
            }).then(function (result) {
                self.menudeleted = [];
                self.reload_menu();
            });
            return result;
        },
        __getDataEditMenu: function ($el) {
            // let data = [];
            // $el.find('> ._wrapUlEdit > li').map((item) => {
            //     let $li =  $(item), viewDataId = $li.attr("view-data"), subData = this.__getDataEditMenu($li);
            //     if (String(viewDataId).includes("view")) {
            //         data.push({...this.menuObj[viewDataId], parent_id: viewDataId, children: subData || []});
            //     }
            // });
            // return data;
        },
    });

return Menu;

});
