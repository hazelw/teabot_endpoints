from flask import Flask, Response, jsonify, request
from slack_communicator import SlackCommunicator
from models import State
import json

app = Flask(__name__)
slack_communicator_wrapper = SlackCommunicator()


def _cup_puraliser(number_of_cups):
    """Correctly puralises the number of cups remaining

    Args:
        - number_of_cups (int) - Number of cups left in the teapot
    Returns
        - String containing <number of cups> cup / cups
    """
    if number_of_cups == 1:
        return "1 cup"
    return "%s cups" % number_of_cups


@app.route("/teaReady", methods=["POST"])
def teaReady():
    """POST'ing to this endpoint triggers a message to be sent to Slack
    alerting everyone that a teapot is ready with X number of cups in it.

    Args:
        - num_of_cups (int) - The number of cups in the teapot
    Returns
        - 200
    """
    data = json.loads(request.data)
    number_of_cups = data["num_of_cups"]
    slack_communicator_wrapper.post_message_to_room(
        "@here The Teapot :teapot: is ready with %s" % _cup_puraliser(
            number_of_cups)
    )
    return Response()


@app.route("/storeState", methods=['POST'])
def storeState():
    """Inserts the state of the teapot into the database

    Args:
        - state (string) - The current state of the teapot
        - timestamp (string) - The time that this state happened
        - num_of_cups (int) - The number of cups left in the teapot
    Returns
        - 200
    """
    data = json.loads(request.data)
    State.create(
        state=data["state"],
        timestamp=data["timestamp"],
        num_of_cups=data["num_of_cups"]
    )
    return Response()


def _human_teapot_state(state):
    base_text = 'There %s %s left' % \
        (_are_or_is(state.num_of_cups), _cup_puraliser(state.num_of_cups))
    if state.state == "COLD_TEAPOT":
        base_text += " but the teas cold :("
    return base_text


def _are_or_is(number_of_cups):
    if number_of_cups == 1:
        return "is"
    return "are"


@app.route("/teabotWebhook", methods=["POST"])
def webhook():
    """Listens for POSTs from Slack, which are requests for the current
    state of the teapot.

    Args:
        - None
    Returns
        - JSON payload
            - text (string) - Describing the current state of the teapot
    """
    latest_state = State.get_newest_state()
    if latest_state:
        return jsonify(
            {
                'text': _human_teapot_state(latest_state)
            }
        )
    else:
        return jsonify({'text': 'Theres no teapot data :('})


@app.route("/imATeapot")
def imATeapot():
    """Bonus endpoint that returns a HTTP 418 I'm a teapot"""
    return Response(), 418


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=True, port=8000)
