
webdnd.subscribe('/sessions/new', function(data) {
    webdnd.user.key(data.key);
    webdnd.user.name(data.name);

    data = {name: 'system', body: data.name + ' just joined us'};
    $(Handlebars.templates.message(data))
        .addClass('notification')
        .css('opacity', 0)
        .appendTo('#messages')
        .animate({
            opacity: 1
        });
});

webdnd.subscribe('/messages/new', function(data) {
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
            left: 0
        });

});

webdnd.subscribe('/messages/started-typing', function(data) {
    // handle started typing
    data = {name: data['name'], body: 'started typing...'};
    $(Handlebars.templates.message(data))
        .addClass('typing')
        .css('opacity', 0)
        .appendTo('#messages')
        .animate({
            opacity: 1
        });
});

webdnd.subscribe('/messages/stopped-typing', function(data) {
   $('.typing').remove();
});

$(function() {
    webdnd.user.name('anon');

    // auto focus to the chat body when loading the page
    $('#form input[name=body]').focus();

    // send messages when form is changed
    $('#form form').submit(function(e) {
        e.preventDefault();

        // notify that typing has stopped
        webdnd.publish('/messages/stopped-typing', {
            name: webdnd.user.name(),
            key: webdnd.user.key()
        });

        var data = {
            name: webdnd.user.name(),
            key: webdnd.user.key(),
            body: $(this).find('input[name=body]').val()
        };

        // send message
        webdnd.publish('/messages/new', data);

        // reset form
        $(this).find('input[name=body]').val('');
    });

    // track typing
    var typing = false;
    $('#form input[name=body]').keyup(function(e) {
        // notify that typing has started
        if ($(this).val().length === 0) {
            typing = false;
            webdnd.publish('/messages/stopped-typing', {
                name: webdnd.user.name()
            });
        } else if ($(this).val().length > 0 && typing === false) {
            typing = true;
            webdnd.publish('/messages/started-typing', {
                name: webdnd.user.name()
            });
        }
    });

});