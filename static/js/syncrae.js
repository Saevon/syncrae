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

syncrae.retry_timer = (function() {
    // Time in sec
    var timer = 10;
    var _timer = 0;

    var _listeners = [];

    var retry_timer = {
        time: function() {
            return _timer;
        },
        timeout: function(val) {
            if (val !== undefined) {
                timer = val;
            } else {
                return timer;
            }
        },
        count: function() {
            _timer -= 1;
            var length = _listeners.length;
            for (var i=0; i< length; i++) {
                _listeners[i](_timer);
            }
        },
        reset: function() {
            _timer = timer;
        },
        listen: function(callback) {
            _listeners.push(callback);
        }
    };

    return retry_timer;
})();

syncrae.connect = function(retry) {
    // Block connection attempts unless they're past the re-connect timer
    if (syncrae.retry_timer.time() > 0) {
        syncrae.retry_timer.count();
        if (retry === true) {
            setTimeout(function() {
                syncrae.connect(true);
            }, 1000);
        }
        return;
    } else {
        syncrae.retry_timer.reset();
    }

    var websocket = new WebSocket('ws://' + HOST + '/event');

    $.extend(websocket, {
        onclose: function(event) {
            syncrae.off(true);
            syncrae.connect(true);
        },
        onopen: function(event) {
            syncrae.on(true);
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

    syncrae.websocket = websocket;
};
syncrae.connect();

syncrae.on = (function() {
    var _callbacks = [];
    var on = function(callback) {
        if (callback === true) {
            var length = _callbacks.length;
            for (var i=0; i < length; i++) {
                _callbacks[i]();
            }
        } else {
            _callbacks.push(callback);
        }
    };
    return on;
})();
syncrae.off = (function() {
    var _callbacks = [];
    var off = function(callback) {
        if (callback === true) {
            var length = _callbacks.length;
            for (var i=0; i < length; i++) {
                _callbacks[i]();
            }
        } else {
            _callbacks.push(callback);
        }
    };
    return off;
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
