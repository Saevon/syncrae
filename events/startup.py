from webdnd_api import Api
from events.event import Event

def user(websocket):
    call = Api(websocket.session.key(), 'account/user/self')

    if call.has_error:
        return {
            'name': 'Unknown'
        }

    event = Event('/sessions/name', {
        'name': call.response['name']
    })
    websocket.write_message(event.to_json())

    return call.response
