odoo.define('izi_dashboard.IZIAutocomplete', function (require) {
    "use strict";

    var Widget = require('web.Widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var view_dialogs = require('web.view_dialogs');
    var QWeb = core.qweb;
    var _t = core._t;
    
    class IZIAutocomplete {
        constructor(parent, args) {
            var self = this;
            self.parent = parent;
            self.elm = args.elm;
            self.multiple = args.multiple;
            self.placeholder = args.placeholder;
            self.params = args.params;
            self.initData = args.initData || (args.multiple ? [] : {});
            self.formatFunc = function format(item) { 
                return item[self.params.textField || 'name']; 
            }
            self.onChange = args.onChange;
            self.selectedId;
            self.selectedText = '';
            if (args.minimumInput)
                self.minimumInputLength = 1;
            else
                self.minimumInputLength = 0;
            self.data = args.data;
            if (self.data)
                self.initWithData();
            else
                self.initWithQuery();
            self.initOnChange();
        }
        set(key, value) {
            var self = this;
            self[key] = value;
        }
        setDomain(domain) {
            var self = this;
            self.params.domain = domain;
            self.initWithQuery();
        }
        destroy() {
            var self = this;
            self.elm.select2('destroy');
        }
        initWithData(){
            var self = this;
            var typingTimer;
            var loadingRPC = false;
            var data = self.data;
            if (!self.multiple) {
                var clearOption = {
                    'id': null,
                    'value': null,
                    'name': 'All',
                }
                data = [clearOption].concat(data);
            }
            self.elm.select2({
                multiple: self.multiple,
                allowClear: true, 
                tokenSeparators: [',', ' '], 
                minimumResultsForSearch: 10, 
                placeholder: self.placeholder,
                minimumInputLength: self.minimumInputLength,
                data: { results: data, text: self.params.textField || 'name' },
            })
        }
        initWithQuery(){
            var self = this;
            var typingTimer;
            var loadingRPC = false;
            self.elm.select2({
                multiple: self.multiple,
                allowClear: true, 
                tokenSeparators: [',', ' '], 
                minimumResultsForSearch: 10, 
                placeholder: self.placeholder,
                minimumInputLength: self.minimumInputLength,
                initSelection: function(element, callback) {
                    // Initialize with empty data or initial data if provided
                    callback(self.initData);
                },
                query: function (query) {
                    var data = {results: []};
                    var domain = [[self.params.textField, 'ilike', query.term]];
                    if (Array.isArray(self.params.domain)  && self.params.domain.length)
                        Array.prototype.push.apply(domain, self.params.domain)
                    clearTimeout(typingTimer);
                    if (query && !loadingRPC) {
                        typingTimer = setTimeout(function() {
                            //do something
                            loadingRPC = true;
                            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                                model: self.params.model,
                                method: 'search_read',
                                args: [domain, self.params.fields],
                                kwargs: {
                                    limit: self.params.limit,
                                },
                            }).then(function (results) {
                                // console.log('Query', query.term);
                                // console.log('RPC', results);
                                var data = results;
                                if (!self.multiple) {
                                    var clearOption = {
                                        'id': null,
                                        'value': null,
                                        'name': 'All',
                                    }
                                    data = [clearOption].concat(data);
                                }
                                query.callback({results: data});
                                loadingRPC = false;
                            });
                        }, 500);
                    }
                    
                },
            })
        }
        initOnChange() {
            var self = this;
            self.elm.on("change", function (e) {
                if (e.added) {
                    self.selectedText = e.added[self.params.textField];
                }
                // If e.val Is Array
                if (Array.isArray(e.val)) {
                    // Check If All Elements of e.val Can Be Parsed To Integer
                    var data = e.val;
                    var isInt = data.every(function (item) {
                        return !isNaN(item);
                    });
                    if (isInt) {
                        self.selectedId = data.map(function (item) {
                            return parseInt(item);
                        });
                    } else {
                        self.selectedId = data;
                    }
                } else {
                    // If e.val Is Not Array
                    if (e.val) {
                        // Check If e.val Can Be Parsed To Integer
                        if (!isNaN(e.val)) {
                            self.selectedId = parseInt(e.val);
                        } else {
                            self.selectedId = e.val;
                        }
                    } else {
                        self.selectedId = null;
                    }
                }
                if (!self.selectedId) {
                    self.selectedText = '';
                }
                self.onChange(self.selectedId, self.selectedText);
            })
        }
    }
    return IZIAutocomplete;
})
