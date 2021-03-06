syncrae = {};

syncrae.listeners = {
    '/': []
};
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
    // Time array
    var timer = [
        // Format: time=secs, count=times to use this time
        // -1 means infinity
        {time: 5, count: 2},
        {time: 10, count: 6},
        {time: 60, count: 10},
        {time: -1, count: -1}
    ];
    var left = $.extend([], timer);
    var _timer = 0;

    var disabled = false;

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
            if (!disabled) {
                _timer -= 1;
            }
            this.tell();
            return !disabled;
        },
        tell: function() {
            var length = _listeners.length;
            for (var i=0; i< length; i++) {
                _listeners[i](_timer);
            }
        },
        reset: function() {
            disabled = false;
            left = $.extend([], timer);

            this.tell();
        },
        trying: function() {
            if (left[0] === undefined || left[0].time <= -1) {
                this.disable();
                return;
            }

            _timer = left[0].time;

            if (left[0].count != -1) {
                left[0].count -= 1;
            }
            if (left[0].count === 0) {
                left.shift();
            }
        },
        listen: function(callback) {
            _listeners.push(callback);
        },
        disable: function() {
            disabled = true;
            _timer = '∞';
            this.tell();
        }
    };

    return retry_timer;
})();

syncrae.connect = function(retry) {
    // Block connection attempts unless they're past the re-connect timer
    var time = syncrae.retry_timer.time();
    if (typeof(time) == 'string' || time > 0) {
        // if count() returns false, the counter has just been disabled
        if (syncrae.retry_timer.count() && retry === true) {
            setTimeout(function() {
                syncrae.connect(true);
            }, 1000);
        }
        return;
    } else {
        syncrae.retry_timer.trying();
    }

    var websocket = new WebSocket('ws://' + HOST + '/event');

    // Allows the debug toolbar to get messages from before it is
    // initialized
    var storage= [];
    var storing = true;
    var store = {
        read: function() {
            var tmp = $.extend([], storage);
            storage = [];
            storing = false;
            return tmp;
        },
        add: function(data) {
            if (storing) {
                storage.push(data);
            }
        }
    };

    $.extend(websocket, {
        onclose: function(event) {
            syncrae.off(true);
            syncrae.connect(true);
        },
        onopen: function(event) {
            syncrae.retry_timer.reset();
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

            store.add(message);

            // Don't forget the base handler
            syncrae.listeners['/'].each(function(callback) {
                callback(message.data, message.topic);
            });
        }
    });

    syncrae.storage = store;
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
