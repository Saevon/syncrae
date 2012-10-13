# from webdnd_api import Api
from syncrae.events.event import Event

def user(websocket):
    call = Api(websocket.session.key(), 'account/user/self')

    if call.has_error:
        return {
            'name': 'Unknown',
            'cname': 'Unknown Campaign',
        }

    Event('/sessions/name', {
        'name': call.response['name'],
        'cname': call.response['campaign_name'],
    }).write_message(websocket)

    return call.response
