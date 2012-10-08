webdnd.listeners =[];
webdnd.queue = (function() {
    var queue = {
        _queue: [],
        _keyed: false,

        send: function(payload) {
            this._queue.push(payload);
            this.sendall();
        },

        keyed: function() {
            this._keyed = true;
            this.sendall();
        },

        _send: function(payload) {
            payload.key = webdnd.user.key();
            message = JSON.stringify(payload);
            webdnd.websocket.send(message);
        },

        sendall: function() {
            if (this._keyed && webdnd.websocket && webdnd.websocket.readyState == 1) {
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

webdnd.websocket = (function() {
    var websocket = new WebSocket('ws://' + HOST + '/event');

    $.extend(websocket, {
        onclose: function(event) {
            // TODO: reestablish connection
        },
        onopen: function(event) {
            webdnd.queue.sendall();
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
    var payload = {'topic': topic, 'data': data};
    this.queue.send(payload);
};

webdnd.subscribe = function(topic, callback) {
    // server side subscription
    this.publish('/subscribe', topic);

    // local subscription
    if(!this.listeners[topic]){
        this.listeners[topic] = [];
    }
    this.listeners[topic].push(callback);
};

window.onbeforeunload = function() {
    webdnd.websocket.close();
};
