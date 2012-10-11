webdnd.user = (function() {
    var _key = '';
    var _name = '';
    var _cname = '';

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
        },
        cname: function(name) {
            if (name !== undefined) {
                _cname = name;
                return this;
            }
            return _cname;
        }

    };

    return user;
})();
