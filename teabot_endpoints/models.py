from peewee import Model, DateTimeField, OperationalError, CharField, \
    IntegerField, ForeignKeyField
from playhouse.sqlite_ext import SqliteExtDatabase
from datetime import datetime

db = SqliteExtDatabase('teapot.db')


class BaseModel(Model):
    class Meta:
        database = db


class PotMaker(BaseModel):
    """Table that records people who can claim to have made a teapot and stats
    about their teapot making
    """
    name = CharField()
    number_of_pots_made = IntegerField()
    total_weight_made = IntegerField()
    number_of_cups_made = IntegerField()
    largest_single_pot = IntegerField()

    @classmethod
    def get_all(cls):
        """Returns all the pot makers

        Args:
            - None
        Returns:
            - list of PotMakers objects
        """
        return [pot_maker for pot_maker in PotMaker.select()]

    @classmethod
    def get_single_pot_maker(cls, name):
        """Returns the pot maker with the given name

        Args:
            - name (String) - Name of pot maker you want to retrieve
        Returns:
            - list of PotMakers objects
        """
        return PotMaker.select().where(
            PotMaker.name == name
        )[0]


class State(BaseModel):
    """Table that records the state of the teapot over time, commonly queried
    for the latest entry to tell people about the state of the teapot
    """
    state = CharField()
    timestamp = DateTimeField(default=datetime.now, index=True)
    num_of_cups = IntegerField()
    weight = IntegerField(null=True)
    temperature = IntegerField(null=True)
    claimed_by = ForeignKeyField(PotMaker, null=True)

    @classmethod
    def get_newest_state(cls):
        """Returns the row from the State table with the newest timestamp
        that represents the last known state of the teapot.

        Args:
            - None
        Returns:
            - state (State) - Row containing details on the state of the teapot
        """
        try:
            return State.select().order_by(-State.timestamp)[0]
        except IndexError:
            return None

    @classmethod
    def get_number_of_new_teapots(cls):
        """Returns the number of new teapots made

        Args:
            - None
        Returns:
            - int - number of new teapots
        """
        return len([s for s in State.select().where(
            State.state == 'FULL_TEAPOT')]
        )

    @classmethod
    def get_latest_full_teapot(cls):
        """Returns the latest FULL_TEAPOT

        Args:
            - None
        Returns:
            - int - age of teapot in minutes
        """
        return State.select().where(
            State.state == 'FULL_TEAPOT').order_by(-State.timestamp)[0]


if __name__ == "__main__":
    try:
        State.create_table()
    except OperationalError:
        print "The table already exists"
    try:
        PotMaker.create_table()
    except OperationalError:
        print "The table already exists"
