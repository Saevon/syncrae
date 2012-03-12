Array.prototype.each = Array.prototype.forEach;

var App = {
    listeners: {},
    queue: [],
    websocket: new WebSocket('ws://' + HOST + '/e')
};

App.websocket.onclose = function(event) {
    // todo: reestablish connection
}

App.websocket.onopen = function(event) {
    App.queue.each(function(message) {
        App.websocket.send(message);
    });
    App.queue = [];
}

App.websocket.onmessage = function(event) {
    var message = JSON.parse(event.data);
    if (message.topic in App.listeners) {
        App.listeners[message.topic].each(function(callback) {
            callback(message.data);
        });
    }
};

App.publish = function(topic, data) {
    var payload = {'topic': topic, 'data': data};
    var message = JSON.stringify(payload);
    if (this.websocket && this.websocket.readyState == 1) {
        this.websocket.send(message);
    } else {
        this.queue.push(message);
    }
};

App.subscribe = function(topic, callback) {
    // server side subscription
    this.publish('/subscribe', topic);

    // local subscription
    if(!this.listeners[topic]){
        this.listeners[topic] = [];
    }
    this.listeners[topic].push(callback);
};

App.subscribe('/sessions/new', function(data) {
    data = {name: 'system', body: data.name + ' just joined us'};
    $(Handlebars.templates.message(data))
        .addClass('notification')
        .css('opacity', 0)
        .appendTo('#messages')
        .animate({
            opacity: 1,
        });
});

App.subscribe('/messages/new', function(data) {
    // idea... if the message comes from you it should
    // slide in from the bottom up
    // if it comes from someone else it slides in from the side
    var message = $(Handlebars.templates.message(data))
        .css('opacity', 0)
        .css('position', 'relative')
        .css('left', '-200px')
        .appendTo('#messages')
        .animate({
            opacity: 1,
            left: 0,
        });

});

App.subscribe('/messages/started-typing', function(data) {
    // handle started typing
    data = {name: data['name'], body: 'started typing...'};
    $(Handlebars.templates.message(data))
        .addClass('typing')
        .css('opacity', 0)
        .appendTo('#messages')
        .animate({
            opacity: 1,
        });
});

App.subscribe('/messages/stopped-typing', function(data) {
   $('.typing').remove();
});

$(function() {
    // auto focus to the chat body when loading the page
    $('#form input[name=body]').focus();

    // send messages when form is changed
    $('#form form').submit(function(e) {
        e.preventDefault();

        // notify that typing has stopped
        App.publish('/messages/stopped-typing', {
            name: 'anon',
        });

        var data = {
            name: 'anon', 
            body: $(this).find('input[name=body]').val()
        };

        // send message
        App.publish('/messages/new', data);

        // reset form
        $(this).find('input[name=body]').val('');
    });

    // track typing
    var typing = false;
    $('#form input[name=body]').keyup(function(e) {
        // notify that typing has started
        if ($(this).val().length == 0) {
            typing = false;
            App.publish('/messages/stopped-typing', {
                name: 'anon',
            });
        } else if ($(this).val().length > 0 && typing == false) {
            typing = true;
            App.publish('/messages/started-typing', {
                name: 'anon',
            });
        }
    });

});