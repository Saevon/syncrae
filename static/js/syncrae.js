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
    // Time array
    var timer = [
        // Format: time=secs, count=times to use this time
        // -1 means infinity
        {time: 2, count: 2},
        {time: 10, count: 30},
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
            if (disabled) {
                return false;
            }

            _timer -= 1;
            var length = _listeners.length;
            for (var i=0; i< length; i++) {
                _listeners[i](_timer);
            }
            return true;
        },
        reset: function() {
            disabled = false;
            left = $.extend([], timer);

            this.trying();
        },
        trying: function() {
            if (left[0] === undefined) {
                disabled = true;
                return;
            }

            _timer = left[0].time;

            if (left[0].count != -1) {
                left[0].count -= 1;
            }
            if (left[0].count === 0) {
                left.shift();
            }

            if (_timer == -1) {
                disabled = true;
            }
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
