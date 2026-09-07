odoo.define('project_task_timer_app.play_suggestion', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var sAnimation = require('project_task_timer_app.play_menu');

    var QWeb = core.qweb;
    var _t = core._t;

    var ajax = require('web.ajax');
    
    sAnimation.include({    
        _startTimeCounter: function () {
             var self = this;
        clearTimeout(this.timer);
            this.timer = setTimeout(function () {
                self.duration += 1000;
                self._startTimeCounter();
            }, 1000);
        this.$el.html($('<span style="color:red;">' + moment.utc(this.duration).format("HH:mm:ss") + '</span>'));
        },
    });
});;
