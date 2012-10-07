webdnd.listeners =[];
webdnd.queue = [];

webdnd.websocket = (function() {
    var websocket = new WebSocket('ws://' + HOST + '/event?key=' + encodeURIComponent(webdnd.user.key()));

    $.extend(websocket, {
        onclose: function(event) {
            // TODO: reestablish connection
        },
        onopen: function(event) {
            webdnd.queue.each(function(message) {
                webdnd.websocket.send(message);
            });
            webdnd.queue = [];
        },

        onmessage: function(event) {
            var message = JSON.parse(event.data);
            if (message.topic in webdnd.listeners) {
                webdnd.listeners[message.topic].each(function(callback) {
                    callback(message.data);
                });
            }
        }
    });

    return websocket;
})();


webdnd.publish = function(topic, data) {
    var payload = {'topic': topic, 'data': data, 'key': webdnd.user.key()};
    var message = JSON.stringify(payload);
    if (this.websocket && this.websocket.readyState == 1) {
        this.websocket.send(message);
    } else {
        this.queue.push(message);
    }
};

webdnd.subscribe = function(topic, callback) {
    // server side subscription
    this.publish('/subscribe', topic);

    var new_callback = function(data) {
        if (data.key) {
            webdnd.user.key(data.key);
        }
        callback(data);
    };

    // local subscription
    if(!this.listeners[topic]){
        this.listeners[topic] = [];
    }
    this.listeners[topic].push(new_callback);
};

window.onbeforeunload = function() {
    webdnd.websocket.close();
};
