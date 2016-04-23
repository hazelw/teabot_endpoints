from flask import Flask, Response, jsonify, request
from SlackCommunicator import SlackCommunicator
from models import State, Config
from settings import DEBUG
import json

app = Flask(__name__)
slack_communicator = SlackCommunicator()


@app.route("/teaReady")
def teaReady():
    data = json.loads(request.data)
    number_of_cups = data["num_of_cups"]
    slack_communicator.post_message_to_room(
        "Teapot is ready with %s cups" % number_of_cups)
    return Response()


@app.route("/getConfig")
def getConfig():
    config = Config.select()[0]
    return jsonify({
        'empty_teapot_weight': config.empty_teapot_weight,
        'weight_of_tea_in_cup': config.weight_of_tea_in_cup,
        'empty_cup_weight': config.empty_cup_weight,
        'full_teapot_weight': config.full_teapot_weight,
        'full_cup_weight': config.full_cup_weight,
        'cold_teapot_temp': config.cold_teapot_temp
    })


@app.route("/setConfig", methods=['POST'])
def setConfig():
    data = json.loads(request.data)
    Config.create(
        empty_teapot_weight=int(data["empty_teapot_weight"]),
        weight_of_tea_in_cup=int(data["weight_of_tea_in_cup"]),
        empty_cup_weight=int(data["empty_cup_weight"]),
        full_teapot_weight=int(data["full_teapot_weight"]),
        full_cup_weight=int(data["full_cup_weight"]),
        cold_teapot_temp=int(data["cold_teapot_temp"])
    )
    return Response()


@app.route("/storeState", methods=['POST'])
def storeState():
    data = json.loads(request.data)
    State.create(
        state=data["state"],
        timestamp=data["timestamp"],
        cups=data["cups"]
    )
    return Response()


@app.route("/getState")
def getState():
    time_to = request.args["timestamp_to"]
    time_from = request.args["timestamp_from"]
    results = [s for s in State.select().where(
        State.timestamp <= time_to & State.timestamp > time_from
    )]
    response = {'results': []}
    for result in results:
        response["results"].append({
            'state': result.state,
            'timestamp': result.timestamp,
            'cups': result.cups
        })
    return jsonify(response)


@app.route("/webhook")
def webhook():
    print "webhook yo", vars(request)
    return Response()


if __name__ == "__main__":
    app.run(debug=DEBUG)
