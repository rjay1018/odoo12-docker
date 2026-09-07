odoo.define('cml_client_profile.website', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');

    $('#next_personal_info').on("click", function (event) {
        $('#personal_information_menu')[0].click();
    });

   $('#support_ids_list').on("change", function (event) {
        var sel_options = event.currentTarget.selectedOptions
        var options = event.currentTarget.options
        var list = []
        for (var i = 0; i < options.length; i++) {
            options[i].value = options[i].id
        }
        for (var i = 0; i < sel_options.length; i++) {
            list.push(sel_options[i].value)
        }
        sel_options[0].value = list.toString()
    });

    $('#next_intake').on("click", function (event) {
        $('#in_take_form_menu')[0].click()
    });

    $('#modal_pop_Contacts_update').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget)
        var name = button.data('contact_name')
        var number = button.data('contact_number')
        var relationship = button.data('contact_relationship')
        var url = button.data('contact_url')
        var delete_url = button.data('contact_delete_url')
        var modal = $(this)
        modal.find('#pop_update_contact')[0].name = url
        modal.find('#pop_delete_contact')[0].name = delete_url
        modal.find('.modal-body #update_name').val(name)
        modal.find('.modal-body #update_contact_number').val(number)
        modal.find('.modal-body #update_relationship').val(relationship)
    });

    $('#pop_update_contact').on("click", function (event) {
        var url = event.currentTarget.name
        var name = $('#update_name')[0].value
        var contact_number = $('#update_contact_number')[0].value
        var relationship = $('#update_relationship')[0].value
        rpc.query({
            route: url,
            params: {
                'name' : name,
                'contact_number' : contact_number,
                'relationship' : relationship
            }
        }).then(function (result) {
            $('#table_responsive').load(location.href + " #table_responsive");
            $('#pop_update_contact_close')[0].click();
        });
    });

    $('#pop_delete_contact').on("click", function (event) {
        var url = event.currentTarget.name
        rpc.query({
            route: url,
            params: {}
        }).then(function (result) {
            $('#table_responsive').load(location.href + " #table_responsive");
            $('#pop_update_contact_close')[0].click();
        });
    });

    $('#pop_add_contact').on("click", function (event) {
        var url = event.currentTarget.name
        var name = $('#add_name')[0].value
        var contact_number = $('#add_contact_number')[0].value
        var relationship = $('#add_relationship')[0].value
        rpc.query({
            route: url,
            params: {
                'name' : name,
                'contact_number' : contact_number,
                'relationship' : relationship
            }
        }).then(function (result) {
            $('#add_name')[0].value = null;
            $('#add_contact_number')[0].value = null;
            $('#add_relationship')[0].value = null;
            $('#table_responsive').load(location.href + " #table_responsive");
            $('#pop_add_contact_close')[0].click();
        });
    });

});