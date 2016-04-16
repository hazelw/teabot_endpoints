from slacker import Slacker

API_TOKEN = 'xoxp-35262207606-35262207622-35222979347-b4cffef4fd'


class SlackCommunicator(object):

    def __init__(self):
        self.slack = Slacker(API_TOKEN)

    def post_message_to_room(self, message):
        self.slack.chat.post_message('#teapot', message)
