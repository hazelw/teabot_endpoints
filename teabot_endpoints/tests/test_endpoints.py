from unittest import TestCase
from playhouse.test_utils import test_database
from teabot_endpoints.models import State, PotMaker, \
    SlackMessages
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
        with test_database(test_db, [State, PotMaker, SlackMessages]):
            super(TestEndpoints, self).run(result)

    def test_im_a_teapot(self):
        result = self.app.get("/imATeapot")
        self.assertTrue(result)
        self.assertEqual(result.status_code, 418)

    @patch(
        "teabot_endpoints.endpoints.slack_communicator_wrapper",
        auto_spec=True)
    def test_tea_ready_no_claim(self, mock_slack):
        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime.now().isoformat(),
            num_of_cups=3
        )
        result = self.app.post("/teaReady")
        self.assertEqual(result.status_code, 200)
        mock_slack.post_message_to_room.assert_any_call(
            "The Teapot :teapot: is ready with 3 cups"
        )
        reaction_message = \
            "Want a cup of tea from the next teapot ? " + \
            "React to this message to let everyone know!"
        mock_slack.post_message_to_room.assert_any_call(
            reaction_message, True)

        self.assertEqual(mock_slack.post_message_to_room.call_count, 2)

    @patch(
        "teabot_endpoints.endpoints.slack_communicator_wrapper",
        auto_spec=True)
    def test_tea_ready_claimed(self, mock_slack):
        maker = PotMaker.create(
            name='bob',
            number_of_pots_made=1,
            total_weight_made=12,
            number_of_cups_made=5,
            largest_single_pot=2
        )
        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime.now().isoformat(),
            num_of_cups=3,
            claimed_by=maker
        )
        result = self.app.post("/teaReady")
        self.assertEqual(result.status_code, 200)
        mock_slack.post_message_to_room.assert_any_call(
            "The Teapot :teapot: is ready with 3 cups, thanks to bob"
        )
        reaction_message = \
            "Want a cup of tea from the next teapot ? " + \
            "React to this message to let everyone know!"
        mock_slack.post_message_to_room.assert_any_call(
            reaction_message, True)

        self.assertEqual(mock_slack.post_message_to_room.call_count, 2)

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
        now = datetime.now()
        result = self.app.post(
            "/storeState",
            data=json.dumps({
                'num_of_cups': 3,
                'timestamp': now.isoformat(),
                'state': 'TEAPOT FULL'
            })
        )
        self.assertEqual(result.status_code, 200)
        database_entries = [d for d in State.select()]
        self.assertEqual(len(database_entries), 1)
        db_entry = database_entries[0]
        self.assertEqual(type(db_entry.timestamp), datetime)
        self.assertEqual(db_entry.num_of_cups, 3)
        self.assertEqual(db_entry.timestamp, now)
        self.assertEqual(db_entry.state, 'TEAPOT FULL')

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

    @patch("teabot_endpoints.endpoints._get_current_time", autospec=True)
    def test_teapot_age(self, mock_time):
        mock_time.return_value = datetime(2016, 1, 1, 12, 5, 0)
        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime(2016, 1, 1, 12, 0, 0),
            num_of_cups=2
        )
        result = self.app.get(
            "/teapotAge",
        )
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data["teapotAge"], 5)

    def test_pot_makers(self):
        PotMaker.create(
            name='aaron',
            number_of_pots_made=1,
            total_weight_made=12,
            number_of_cups_made=5,
            largest_single_pot=2
        )
        PotMaker.create(
            name='bob',
            number_of_pots_made=1,
            total_weight_made=12,
            number_of_cups_made=5,
            largest_single_pot=2
        )
        result = self.app.get('/potMakers')
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(len(data['potMakers']), 2)

    def test_claim_pot_already_claimed(self):
        maker = PotMaker.create(
            name='bob',
            number_of_pots_made=1,
            total_weight_made=12,
            number_of_cups_made=5,
            largest_single_pot=2
        )
        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime(2016, 1, 1, 12, 0, 0),
            num_of_cups=2,
            claimed_by=maker
        )
        result = self.app.post('/claimPot')
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['submitMessage'], 'Pot has already been claimed')

    def test_claim_pot_unclaimed(self):
        maker = PotMaker.create(
            name='bob',
            number_of_pots_made=1,
            total_weight_made=12,
            number_of_cups_made=5,
            largest_single_pot=2
        )
        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime(2016, 1, 1, 12, 0, 0),
            num_of_cups=5,
            weight=10
        )
        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime(2017, 1, 1, 12, 0, 0),
            num_of_cups=2,
            weight=5
        )
        result = self.app.post(
            '/claimPot',
            data=json.dumps({
                'potMaker': 'bob',
            })
        )
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['submitMessage'], 'Pot claimed, thanks, bob')

        updated_pot_maker = PotMaker.get_single_pot_maker(
            'bob'
        )
        self.assertEqual(updated_pot_maker.number_of_pots_made, 2)
        self.assertEqual(updated_pot_maker.total_weight_made, 17)
        self.assertEqual(updated_pot_maker.number_of_cups_made, 7)
        self.assertEqual(updated_pot_maker.largest_single_pot, 5)

        updated_state = State.get_latest_full_teapot()
        self.assertEqual(updated_state.claimed_by, maker)

    def test_claim_pot_no_pot_maker(self):
        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime(2016, 1, 1, 12, 0, 0),
            num_of_cups=2,
            claimed_by=None
        )
        result = self.app.post('/claimPot', data=json.dumps({}))
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(
            data['submitMessage'], 'You need to select a pot maker')

    def test_leaderboard_gets_all_results_by_default(self):
        maker_1 = PotMaker.create(
            name='bob',
            number_of_pots_made=2,
            total_weight_made=13,
            number_of_cups_made=10,
            largest_single_pot=10
        )
        maker_2 = PotMaker.create(
            name='dave',
            number_of_pots_made=1,
            total_weight_made=10,
            number_of_cups_made=4,
            largest_single_pot=4
        )

        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime(2018, 1, 1, 12, 0, 0),
            num_of_cups=6,
            weight=10,
            claimed_by=maker_1
        )
        State.create(
            state="COLD_TEAPOT",
            timestamp=datetime(2019, 1, 1, 12, 0, 0),
            num_of_cups=4,
            weight=3,
            claimed_by=maker_1
        )
        State.create(
            state='GOOD_TEAPOT',
            timestamp=datetime(2018, 6, 1, 12, 0, 0),
            num_of_cups=4,
            weight=10,
            claimed_by=maker_2
        )

        response = self.app.post('/leaderboard', data=json.dumps({}))

        self.assertEqual(
            json.loads(response.data),
            {'results': [{
                'name': 'bob',
                'inactive': False,
                'largestSinglePot': 10,
                'numberOfCupsMade': 10,
                'numberOfPotsMade': 2,
                'totalWeightMade': 13
            }, {
                'name': 'dave',
                'inactive': False,
                'largestSinglePot': 10,
                'numberOfCupsMade': 4,
                'numberOfPotsMade': 1,
                'totalWeightMade': 10
            }]}
        )

    def test_leaderboard_gets_results_within_time_boundary(self):
        maker_1 = PotMaker.create(
            name='bob',
            number_of_pots_made=2,
            total_weight_made=13,
            number_of_cups_made=10,
            largest_single_pot=10
        )
        maker_2 = PotMaker.create(
            name='dave',
            number_of_pots_made=1,
            total_weight_made=10,
            number_of_cups_made=4,
            largest_single_pot=4
        )

        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime(2018, 1, 1, 12, 0, 0),
            num_of_cups=6,
            weight=10,
            claimed_by=maker_1
        )
        State.create(
            state="COLD_TEAPOT",
            timestamp=datetime(2019, 1, 1, 12, 0, 0),
            num_of_cups=4,
            weight=3,
            claimed_by=maker_1
        )
        State.create(
            state='GOOD_TEAPOT',
            timestamp=datetime(2018, 6, 1, 12, 0, 0),
            num_of_cups=4,
            weight=10,
            claimed_by=maker_2
        )

        request = {
            'from_timestamp': '2018-07-01T00:00:00.000000',
            'to_timestamp': '2020-01-01T00:00:00.000000'
        }
        response = self.app.post('/leaderboard', data=json.dumps(request))

        self.assertEqual(
            json.loads(response.data),
            {'results': [{
                'name': 'bob',
                'inactive': False,
                'largestSinglePot': 3,
                'numberOfCupsMade': 4,
                'numberOfPotsMade': 1,
                'totalWeightMade': 3
            }, {
                'name': 'dave',
                'inactive': False,
                'largestSinglePot': 0,
                'numberOfCupsMade': 0,
                'numberOfPotsMade': 0,
                'totalWeightMade': 0
            }]}
        )
