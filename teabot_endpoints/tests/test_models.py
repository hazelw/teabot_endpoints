from unittest import TestCase
from playhouse.test_utils import test_database
from teabot_endpoints.models import State
from peewee import SqliteDatabase
from datetime import datetime, timedelta

test_db = SqliteDatabase(':memory:')


class TestModels(TestCase):

    def run(self, result=None):
        with test_database(test_db, [State]):
            super(TestModels, self).run(result)

    def test_get_latest_state_none(self):
        result = State.get_newest_state()
        self.assertIsNone(result)

    def test_get_latest_state(self):
        State.create(
            state="TEAPOT_FULL",
            timestamp=datetime.now().isoformat(),
            num_of_cups=3
        )
        State.create(
            state="TEAPOT_EMPTY",
            timestamp=datetime.now() - timedelta(weeks=1),
            num_of_cups=0
        )
        result = State.get_newest_state()
        self.assertEqual(result.state, "TEAPOT_FULL")
        self.assertEqual(result.num_of_cups, 3)

    def test_get_number_of_new_teapots(self):
        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime.now().isoformat(),
            num_of_cups=3
        )
        State.create(
            state="FULL_TEAPOT",
            timestamp=datetime.now() - timedelta(weeks=1),
            num_of_cups=0
        )
        State.create(
            state="EMPTY_TEAPOT",
            timestamp=datetime.now() - timedelta(weeks=1),
            num_of_cups=0
        )
        result = State.get_number_of_new_teapots()
        self.assertEqual(result, 2)
