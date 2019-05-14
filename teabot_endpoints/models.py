from peewee import Model, DateTimeField, OperationalError, CharField, \
    IntegerField, ForeignKeyField, BooleanField
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
    inactive = BooleanField(default=False)
    requested_teapot = BooleanField(default=False, null=True)
    mac_address = CharField(null=True)

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

    @classmethod
    def flip_requested_teapot(cls, mac_address):
        """Flips the value of the requested teapot field for the user with
        name
        Args:
            - mac_address (String) - Mac Address of the dash button for the
            user
        Returns:
            - None
        """
        maker = cls.get_single_pot_maker_by_mac_address(mac_address)
        maker.requested_teapot = not maker.requested_teapot
        maker.save()
        return maker

    @classmethod
    def get_single_pot_maker_by_mac_address(cls, mac_address):
        """Returns the pot maker with the given mac_address dash button

        Args:
            - mac_address (String) - Mac Address of the dash button for the
            user
        Returns:
            - PotMaker object
        """
        return PotMaker.select().where(
            PotMaker.mac_address == mac_address
        )[0]

    @classmethod
    def get_number_of_teapot_requests(cls):
        """Returns the pot maker with the given mac_address dash button

        Args:
            - mac_address (String) - Mac Address of the dash button for the
            user
        Returns:
            - PotMaker object
        """
        return PotMaker.select().where(
            PotMaker.requested_teapot == True  # noqa
        ).count()

    @classmethod
    def reset_teapot_requests(cls):
        makers = PotMaker.get_all()

        for maker in makers:
            maker.requested_teapot = False
            maker.save()


class State(BaseModel):
    """Table that records the state of the teapot over time, commonly queried
    for the latest entry to tell people about the state of the teapot
    """
    state = CharField()
    timestamp = DateTimeField(default=datetime.now, index=True)
    num_of_cups = IntegerField()
    weight = IntegerField(null=True)
    temperature = IntegerField(null=True)
    claimed_by = ForeignKeyField(PotMaker, null=True, index=True)

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


class SlackMessages(BaseModel):
    timestamp = CharField()
    channel = CharField()

    @classmethod
    def store_message_details(cls, timestamp, channel):
        SlackMessages.create(timestamp=timestamp, channel=channel)

    @classmethod
    def get_reaction_message_details(cls):
        message = SlackMessages.select()
        if message:
            return message[0]

    @classmethod
    def clear_slack_message(cls):
        message = SlackMessages.select()
        if message:
            message[0].delete_instance()


if __name__ == "__main__":
    try:
        State.create_table()
    except OperationalError:
        print "The table already exists"
    try:
        PotMaker.create_table()
    except OperationalError:
        print "The table already exists"
    try:
        SlackMessages.create_table()
    except OperationalError:
        print "The table already exists"
