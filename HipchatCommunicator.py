import requests


TEN_SECOND_TIMEOUT = 10.0


class HipchatCommunicator(object):

    def __init__(self, auth_token, room_id, user_name):
        self.auth_token = auth_token
        self.room_id = room_id
        self.user_name = user_name

    def post_message_to_room(self, message):
        endpoint = self.construct_endpoint_url()
        requests.post(
            endpoint, data={"message": message}, timeout=TEN_SECOND_TIMEOUT
        )

    def construct_endpoint_url(self):
        return "https://%s.hipchat.com/v2/room/%s/notification?auth_token=%s" \
            % (self.user_name, self.room_id, self.auth_token)
