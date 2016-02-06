from flask import Flask, Response
from HipchatCommunicator import HipchatCommunicator
from settings import AUTH_TOKEN, ROOM_ID, USER_NAME, DEBUG

app = Flask(__name__)
hipchat_communicator = HipchatCommunicator(
    auth_token=AUTH_TOKEN, room_id=ROOM_ID, user_name=USER_NAME
)


@app.route("/newpot")
def newPot():
    hipchat_communicator.post_message_to_room("Teapot is ready")
    return Response()


@app.route("/lastCall")
def lastCall():
    hipchat_communicator.post_message_to_room(
        "Teapot is about to go cold drink up"
    )
    return Response()


if __name__ == "__main__":
    app.run(debug=DEBUG)
