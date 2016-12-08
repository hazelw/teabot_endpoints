from slacker import Slacker
from settings import API_TOKEN, TEABOT_ROOM
from models import SlackMessages


class SlackCommunicator(object):
    """Handles communicating with Slack"""

    def __init__(self):
        self.slack = Slacker(API_TOKEN)

    def post_message_to_room(self, message, reaction_message=False):
        """Posts a message to the Slack room specified in the settings.

        Args:
            - Message (string) - Message to post to the slack room
        """
        response = self.slack.chat.post_message(TEABOT_ROOM, message)

        if reaction_message:
            message_ts = response.body['ts']
            message_channel = response.body['channel']
            SlackMessages.store_message_details(message_ts, message_channel)

    def get_message_reaction_count(self):
        """Get the counts of reactions on a slack message.

        Args:
            - count (int) - Total reaction count.
        """
        message = SlackMessages.get_reaction_message_details()
        if message:
            response = self.slack.reactions.get(
                channel=message.channel, timestamp=message.timestamp)

        count = 0
        if response:
            if 'reactions' in response.body['message'].keys():
                for reaction in response.body['message']['reactions']:
                    count += reaction['count']
        return count
