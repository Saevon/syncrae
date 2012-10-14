syncrae = {};

syncrae.listeners =[];
syncrae.queue = (function() {
    var queue = {
        _queue: [],

        send: function(payload) {
            this._queue.push(payload);
            this.sendall();
        },

        _send: function(payload) {
            message = JSON.stringify(payload);
            syncrae.websocket.send(message);
        },

        sendall: function() {
            if (syncrae.websocket && syncrae.websocket.readyState == 1) {
                var _this = this;
                this._queue.each(function(payload) {
                    _this._send(payload);
                });
                this._queue = [];
            }
        }
    };

    return queue;
})();

syncrae.websocket = (function() {
    var websocket = new WebSocket('ws://' + HOST + '/event');

    $.extend(websocket, {
        onclose: function(event) {
            // TODO: reestablish connection
        },
        onopen: function(event) {
            syncrae.queue.sendall();
        },

        onmessage: function(event) {
            var message = JSON.parse(event.data);
            if (message.topic in syncrae.listeners) {
                syncrae.listeners[message.topic].each(function(callback) {
                    callback(message.data);
                });
            }
        }
    });

    return websocket;
})();


syncrae.publish = function(topic, data) {
    if (data === undefined) {
        data = {};
    }
    var payload = {'topic': topic, 'data': data};
    this.queue.send(payload);
};

syncrae.subscribe = function(topic, callback) {
    // local subscription adds a callback functions
    if(!this.listeners[topic]){
        this.listeners[topic] = [];
    }
    this.listeners[topic].push(callback);
};

window.onbeforeunload = function() {
    syncrae.websocket.close();
};
