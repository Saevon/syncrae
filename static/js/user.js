webdnd.user = (function() {
    var _key = '';
    var _name = '';

    var user = {

        key: function(key) {
            if (key !== undefined) {
                _key = key;
                return this;
            }
            return _key;
        },

        name: function(name) {
            if (name !== undefined) {
                _name = name;
                return this;
            }
            return _name;
        }
    };

    return user;
})();
