odoo.define('ki_appointment_management.appointment', function (require) {
    "use strict";

    require('web.dom_ready');
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');
    var session = require('web.session');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    var timer = '';

    var rowsShown = 4;
    var rowsTotal = $('#data tbody tr').length;
    var numPages = rowsTotal/rowsShown;
    for(var i = 0;i < numPages;i++) {
        var pageNum = i + 1;
        $('#nav').append('<li class="page-item"><a class="page-link" style="color:black;" href="#" rel="'+i+'">'+pageNum+'</a></li>');
    }
    $('#data tbody tr').hide();
    $('#data tbody tr').slice(0, rowsShown).show();
    $('#nav a:first').addClass('active');
    $('#nav a:first').css( "background-color", "#00A09D" );
    $('#nav a').on('click', function(event){
        $('#slot_id_')[0].setAttribute('value','');
        $('#slot_booking button.slot_allot').removeClass('active');
        $('#nav a').removeClass('active');
        $('#nav a').css( "background-color", "" );
        $(this).addClass('active');
        $(this).css( "background-color", "#00A09D" );
        var currPage = $(this).attr('rel');
        var startItem = currPage * rowsShown;
        var endItem = startItem + rowsShown;
        $('#data tbody tr').css('opacity','0.0').hide().slice(startItem, endItem).
        css('display','table-row').animate({opacity:1}, 300);
    });

    $('#slot_booking button.slot_allot').on('click',function(event){
        $('#slot_booking button.slot_allot').removeClass('active');
        $(this).addClass('active');
        $('#slot_id_')[0].setAttribute('value',$(this).val());
    });

    $('#myDropdown option').on('click',function(event){
        document.getElementById("counselor_id").value = this.value
        document.getElementById("counselor_id_search").value = this.text
        document.getElementById("myDropdown").classList.remove("show");
        $('#onhange_filter_by select').trigger('change')
    });

    $('#counselor_id_search').on('input',function(event) {
        clearTimeout(timer);
        var input, filter, ul, li, a, i,op_div,txtValue;
        document.getElementById("counselor_id").value = '';
        input = document.getElementById("counselor_id_search");
        if (document.getElementById("myDropdown").classList.contains('show')) {
            if (input.value == '') {
                document.getElementById("myDropdown").classList.remove("show");
            }
        }
        else {
            document.getElementById("myDropdown").classList.add("show");
        }
        filter = input.value.toUpperCase();
        op_div = document.getElementById("myDropdown");
        a = op_div.getElementsByTagName("option");
        for (i = 0; i < a.length; i++) {
            txtValue = a[i].textContent || a[i].innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
              a[i].style.display = "";
            } else {
              a[i].style.display = "none";
            }
        }
        timer = setTimeout(function() {
            $('#onhange_filter_by select').trigger('change')
        }, 3000);
    });

/*    $('#client_support_id_search').on('input',function(event) {
        clearTimeout(timer);
        var input, filter, ul, li, a, i,op_div,txtValue;
        document.getElementById("client_support_id").value = '';
        input = document.getElementById("client_support_id_search");
        if (document.getElementById("myDropdown").classList.contains('show')) {
            if (input.value == '') {
                document.getElementById("myDropdown").classList.remove("show");
            }
        }
        else {
            document.getElementById("myDropdown").classList.add("show");
        }
        filter = input.value.toUpperCase();
        op_div = document.getElementById("myDropdown");
        a = op_div.getElementsByTagName("option");
        for (i = 0; i < a.length; i++) {
            txtValue = a[i].textContent || a[i].innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
              a[i].style.display = "";
            } else {
              a[i].style.display = "none";
            }
        }
        timer = setTimeout(function() {
            $('#onhange_filter_by select').trigger('change')
        }, 3000);
    });*/


    /*$('#onhange_filter_by select').on('change',function(event){
        var support_id = document.getElementById("client_support_id").value
        var counselor_id = $('#onhange_filter_by select.counselor_ids').val()
        var slot_id = $('#onhange_filter_by select.slot_ids').val()
        
        $('#calendar td.fc-day').each(function( index ) {
            var date = $(this).data("date");
            rpc.query({
                model: 'hr.employee',
                method: 'get_appointment_availibility',
                args: [support_id,counselor_id,slot_id,date],
            }, {async: false}).then(function (result) {
                if (result == true) {
                    $('#calendar [data-date='+date+']').css({'background': '#90EE90'});
                }
                else if (result == false) {
                    $('#calendar [data-date='+date+']').css({'background': 'none'});
                }
            });
        });
    });*/

    $('#onhange_filter_by select').trigger('change')

    $('#onhange_filter_by select').on('change',function(event){
        var counselor_id = document.getElementById("counselor_id").value
        var support_id = $('#onhange_filter_by select.support_ids').val()
        var slot_id = $('#onhange_filter_by select.slot_ids').val()
        
        $('#calendar td.fc-day').each(function( index ) {
            var date = $(this).data("date");
            rpc.query({
                route: '/web/appointment/filter',
                params: {support_id: support_id, counselor_id:counselor_id, slot_id:slot_id,s_date:date }
            }).then(function (result) {
                if (result == true) {
                    $('#calendar [data-date='+date+']').css({'background': '#90EE90'});
                }
                else if (result == false) {
                    $('#calendar [data-date='+date+']').css({'background': 'none'});
                }
            });
        });
    });



/*    $('#mini_calendar').fullCalendar({
        header: {
            left: 'prev,next',
            center: 'title',
            right: 'today'
        },
        navLinks: false,
        eventLimit: false,
    });

    $('#mini_calendar').on('click',function(event){
        $('#onhange_filter_by select').trigger('change')
    });*/


    $('#calendar').fullCalendar({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek'
        },
        navLinks: false,
        eventLimit: false,
        dayClick: function(calEvent, jsEvent, view) {
            var date = $(this).data("date");
            var d = new Date(String(date));
            var current_date = new Date()
            var current_date_day = current_date.getDate()
            var current_date_month = current_date.getMonth()
            var current_date_year = current_date.getFullYear()
            var day = d.getDate()
            var month = d.getMonth()
            var year = d.getFullYear()
            var support_id = $(".support_ids :selected").val();
            var employee_id = $("#counselor_id").val();
            if (year >= current_date_year) {
                if (month == current_date_month) {
                    if (day >= current_date_day) {
                        window.location.href = "/new/appointment/create/" + day + "?date=" + date + "&sd=" + support_id + "&ed=" + employee_id
                    }
                }
                else if(month > current_date_month) {
                    window.location.href = "/new/appointment/create/" + day + "?date=" + date + "&sd=" + support_id + "&ed=" + employee_id
                }
            }
        },
    });
});