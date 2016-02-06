from peewee import Model, DateTimeField, OperationalError
from playhouse.sqlite_ext import SqliteExtDatabase
from datetime import datetime

db = SqliteExtDatabase('teapot.db')


class BaseModel(Model):
    class Meta:
        database = db


class BrewLog(BaseModel):
    creation_time = DateTimeField(default=datetime.now)


if __name__ == "__main__":
    try:
        BrewLog.create_table()
    except OperationalError:
        print "Brewlog table already exists!"
