from unittest import TestCase
from playhouse.test_utils import test_database
from teabot_endpoints.models import State
from teabot_endpoints.endpoints import app, _cup_puraliser, \
    _human_teapot_state, _are_or_is
from peewee import SqliteDatabase
from mock import patch
import json
from datetime import datetime, timedelta

test_db = SqliteDatabase(':memory:')


class TestEndpoints(TestCase):

    def setUp(self):
        self.app = app.test_client()

    def run(self, result=None):
        with test_database(test_db, [State]):
            super(TestEndpoints, self).run(result)

    def test_im_a_teapot(self):
        result = self.app.get("/imATeapot")
        self.assertTrue(result)
        self.assertEqual(result.status_code, 418)

    @patch(
        "teabot_endpoints.endpoints.slack_communicator_wrapper",
        auto_spec=True)
    def test_tea_ready(self, mock_slack):
        result = self.app.post(
            "/teaReady", data=json.dumps({'num_of_cups': 3})
        )
        self.assertEqual(result.status_code, 200)
        mock_slack.post_message_to_room.assert_called_once_with(
            "@here The Teapot :teapot: is ready with 3 cups"
        )

    def test_tea_webhook_no_data(self):
        result = self.app.post("/teabotWebhook")
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data["text"], "Theres no teapot data :(")

    def test_tea_webhook_data(self):
        State.create(
            state="TEAPOT FULL",
            timestamp=datetime.now().isoformat(),
            num_of_cups=3
        )
        State.create(
            state="TEAPOT EMPTY",
            timestamp=datetime.now() - timedelta(weeks=1),
            num_of_cups=2
        )
        result = self.app.post("/teabotWebhook")
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data["text"], "There are 3 cups left")

    def test_tea_webhook_data_cold_tea(self):
        State.create(
            state="COLD_TEAPOT",
            timestamp=datetime.now().isoformat(),
            num_of_cups=3
        )
        State.create(
            state="TEAPOT EMPTY",
            timestamp=datetime.now() - timedelta(weeks=1),
            num_of_cups=2
        )
        result = self.app.post("/teabotWebhook")
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(
            data["text"], "There are 3 cups left but the teas cold :(")

    def test_store_state(self):
        database_entries = [d for d in State.select()]
        self.assertEqual(len(database_entries), 0)
        result = self.app.post(
            "/storeState",
            data=json.dumps({
                'num_of_cups': 3,
                'timestamp': datetime.now().isoformat(),
                'state': 'TEAPOT FULL'
            })
        )
        self.assertEqual(result.status_code, 200)
        database_entries = [d for d in State.select()]
        self.assertEqual(len(database_entries), 1)

    def test_pluraliser_1_cup(self):
        result = _cup_puraliser(1)
        self.assertEqual(result, "1 cup")

    def test_pluraliser_more_than_1_cup(self):
        result = _cup_puraliser(10)
        self.assertEqual(result, "10 cups")

    def test_human_teapot_state_cold_tea(self):
        state = State.create(
            state="COLD_TEAPOT",
            timestamp=datetime.now().isoformat(),
            num_of_cups=3
        )
        result = _human_teapot_state(state)
        self.assertEqual(result, "There are 3 cups left but the teas cold :(")

    def test_human_teapot_state_cold_tea_one_cup(self):
        state = State.create(
            state="COLD_TEAPOT",
            timestamp=datetime.now().isoformat(),
            num_of_cups=1
        )
        result = _human_teapot_state(state)
        self.assertEqual(result, "There is 1 cup left but the teas cold :(")

    def test_human_teapot_state_good_tea_1_cup(self):
        state = State.create(
            state="TEAPOT_FULL",
            timestamp=datetime.now().isoformat(),
            num_of_cups=1
        )
        result = _human_teapot_state(state)
        self.assertEqual(result, "There is 1 cup left")

    def test_human_teapot_state_good_tea_many_cups(self):
        state = State.create(
            state="TEAPOT_FULL",
            timestamp=datetime.now().isoformat(),
            num_of_cups=2
        )
        result = _human_teapot_state(state)
        self.assertEqual(result, "There are 2 cups left")

    def test_are_or_is_are(self):
        result = _are_or_is(3)
        self.assertEqual(result, "are")

    def test_are_or_is_is(self):
        result = _are_or_is(1)
        self.assertEqual(result, "is")
