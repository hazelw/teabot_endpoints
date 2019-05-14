from flask import Flask, Response, jsonify, request, got_request_exception
import rollbar
import rollbar.contrib.flask
from settings import ROLLBAR_API_TOKEN
import os
from slack_communicator import SlackCommunicator
from models import State, PotMaker, SlackMessages
import json
from datetime import datetime


app = Flask(__name__)
slack_communicator_wrapper = SlackCommunicator()


@app.before_first_request
def init_rollbar():
    """init rollbar module"""
    rollbar.init(
        # api key
        ROLLBAR_API_TOKEN,
        # environment name
        'teabot_webapp',
        # server root directory, makes tracebacks prettier
        root=os.path.dirname(os.path.realpath(__file__)),
        # flask already sets up logging
        allow_logging_basic_config=False
    )

    # send exceptions from `app` to rollbar, using flask's signal system.
    got_request_exception.connect(rollbar.contrib.flask.report_exception, app)


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
    latest_state = State.get_newest_state()
    last_full_pot = State.get_latest_full_teapot()
    number_of_cups = latest_state.num_of_cups
    message = "The Teapot :teapot: is ready with %s" % (
        _cup_puraliser(number_of_cups)
    )
    reaction_message = \
        "Want a cup of tea from the next teapot ? " + \
        "React to this message to let everyone know!"
    if last_full_pot.claimed_by:
        message += ", thanks to %s" % last_full_pot.claimed_by.name
    slack_communicator_wrapper.post_message_to_room(message)
    PotMaker.reset_teapot_requests()
    SlackMessages.clear_slack_message()
    slack_communicator_wrapper.post_message_to_room(reaction_message, True)
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
        timestamp=datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S.%f"),
        num_of_cups=data["num_of_cups"],
        weight=data.get("weight", -1),
        temperature=data.get("temperature", 1)
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


@app.route("/teabotWebhook", methods=["POST", "GET"])
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


@app.route("/numberOfNewTeapots")
def numberOfNewTeapots():
    """Returns a JSON blob containing the total number of teapots made

    Args:
        - None
    Returns
        - {numberOfTeapots: X}
    """
    number_of_teapots = State.get_number_of_new_teapots()
    return jsonify({"numberOfTeapots": number_of_teapots})


def _get_current_time():
    return datetime.now()


@app.route("/teapotAge")
def teapotAge():
    """Returns a JSON blob containing the age of the teapot in minutes

    Args:
        - None
    Returns
        - {teapotAge: X}
    """
    latest_pot = State.get_latest_full_teapot()
    teapot_age = _get_current_time() - latest_pot.timestamp
    teapot_age = teapot_age.total_seconds() / 60

    return jsonify({"teapotAge": teapot_age})


@app.route("/potMakers")
def potMakers():
    """Returns a JSON blob containing details on potmakers

    Args:
        - None
    Returns
        - [{
            name: string,
            numberOfPotsMade: int,
            totalWeightMade: int,
            largestSinglePot: int
            numberOfCupsMade: int
            inactive: bool
        }]
    """
    all_pot_makers = PotMaker.get_all()
    results = []
    for pot_maker in all_pot_makers:
        results.append({
            'name': pot_maker.name,
            'numberOfPotsMade': pot_maker.number_of_pots_made,
            'totalWeightMade': pot_maker.total_weight_made,
            'largestSinglePot': pot_maker.largest_single_pot,
            'numberOfCupsMade': pot_maker.number_of_cups_made,
            'inactive': pot_maker.inactive
        })

    return jsonify({"potMakers": results})


@app.route("/leaderboard", methods=['POST'])
def leaderboard():
    """Returns teapots made by each PotMaker within the specified time period

    Args:
        - from_timestamp: string (format: YYYY-MM-DDThh:mm:ss, optional)
        - to_timestamp: string (format: YYYY-MM-DDThh:mm:ss, optional)
    Returns:
        - [{
            name: string,
            numberOfPotsMade: int,
            totalWeightMade: int,
            largestSinglePot: int
            numberOfCupsMade: int
            inactive: bool
        ]]
    """
    data = json.loads(request.data)
    results = []

    for pot_maker in PotMaker.get_all():
        cups_made = 0
        total_weight = 0
        largest_pot_weight = 0

        from_timestamp = data.get('from_timestamp')
        to_timestamp = data.get('to_timestamp')

        from_datetime = (
            datetime.strptime(from_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
            if from_timestamp else datetime.min
        )
        to_datetime = (
            datetime.strptime(to_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
            if to_timestamp else datetime.max
        )

        teapots = State.select().where(
            State.claimed_by == pot_maker, State.timestamp >= from_datetime,
            State.timestamp < to_datetime
        )

        pots_made = len(teapots)

        for teapot in teapots:
            total_weight = total_weight + teapot.weight
            cups_made = cups_made + teapot.num_of_cups
            largest_pot_weight = max(largest_pot_weight, teapot.weight)

        results.append({
            'name': pot_maker.name,
            'numberOfPotsMade': pots_made,
            'totalWeightMade': total_weight,
            'largestSinglePot': largest_pot_weight,
            'numberOfCupsMade': cups_made,
            'inactive': pot_maker.inactive
        })

    return jsonify({'results': results})


@app.route("/claimPot", methods=['POST'])
def claimPot():
    """Lets a user claim to have made a teapot

    Args:
        - None
    Returns:
        - {'submitMessage': 'Error / Success Message'}
    """
    latest_full_pot = State.get_latest_full_teapot()
    if latest_full_pot.claimed_by:
        return jsonify({'submitMessage': 'Pot has already been claimed'})
    try:
        maker = json.loads(request.data)['potMaker']
    except KeyError:
        return jsonify({'submitMessage': 'You need to select a pot maker'})

    maker = PotMaker.get_single_pot_maker(maker)
    maker.number_of_pots_made += 1
    maker.total_weight_made += latest_full_pot.weight
    maker.number_of_cups_made += latest_full_pot.num_of_cups
    if maker.largest_single_pot < latest_full_pot.weight:
        maker.largest_single_pot = latest_full_pot.weight
    maker.save()
    latest_full_pot.claimed_by = maker
    latest_full_pot.save()
    return jsonify({'submitMessage': 'Pot claimed, thanks, %s' % maker.name})


@app.route("/flipTeapotRequest", methods=['POST'])
def flipTeapotRequest():
    """Lets users reguster / deregister interest in a cup of tea via dash button

    Args:
        None

    Returns:
        {'requestedTeapot': teapot request status}
    """

    data = json.loads(request.data)

    maker = PotMaker.flip_requested_teapot(data['dash_mac_address'])

    return jsonify({'requestedTeapot': maker.requested_teapot})


@app.route("/getNumberOfTeapotRequests", methods=['GET'])
def getNumberOfTeapotRequests():
    """Gets number of teapot requests

    Args:
        None

    Returns:
        {'teaRequests': number of tea requests}

    """
    tea_requests = PotMaker.get_number_of_teapot_requests() + \
        slack_communicator_wrapper.get_message_reaction_count()

    return jsonify({'teaRequests': tea_requests})


if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=True, port=8000)
