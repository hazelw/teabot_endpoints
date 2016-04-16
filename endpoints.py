from flask import Flask, Response, jsonify
from SlackCommunicator import SlackCommunicator
from models import BrewLog
from settings import AUTH_TOKEN, ROOM_ID, USER_NAME, DEBUG

app = Flask(__name__)
slack_communicator = SlackCommunicator()


@app.route("/newpot")
def newPot():
    slack_communicator.post_message_to_room("Teapot is ready")
    BrewLog.create()
    return Response()


@app.route("/lastcall")
def lastCall():
    slack_communicator.post_message_to_room(
        "Teapot is about to go cold drink up"
    )
    return Response()


@app.route("/numpots")
def numberOfPots():
    number_of_pots = BrewLog.select().count()
    return jsonify({"number_of_pots": number_of_pots})


if __name__ == "__main__":
    app.run(debug=DEBUG)
