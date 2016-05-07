from slacker import Slacker
from settings import API_TOKEN, TEABOT_ROOM


class SlackCommunicator(object):
    """Handles communicating with Slack"""

    def __init__(self):
        self.slack = Slacker(API_TOKEN)

    def post_message_to_room(self, message):
        """Posts a message to the Slack room specified in the settings.

        Args:
            - Message (string) - Message to post to the slack room
        """
        self.slack.chat.post_message(TEABOT_ROOM, message)
