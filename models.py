from peewee import Model, DateTimeField, OperationalError, CharField, \
    IntegerField
from playhouse.sqlite_ext import SqliteExtDatabase
from datetime import datetime

db = SqliteExtDatabase('teapot.db')


class BaseModel(Model):
    class Meta:
        database = db


class State(BaseModel):
    state = CharField()
    timestamp = DateTimeField(default=datetime.now)
    cups = IntegerField()


class Config(BaseModel):
    empty_teapot_weight = IntegerField()
    weight_of_tea_in_cup = IntegerField()
    empty_cup_weight = IntegerField()
    full_teapot_weight = IntegerField()
    full_cup_weight = IntegerField()
    cold_teapot_temp = IntegerField()


if __name__ == "__main__":
    try:
        State.create_table()
        Config.create_table()
    except OperationalError:
        print "One or more of the tables still exist"
