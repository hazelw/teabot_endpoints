Teabot Endpoints
================

Endpoints for teabot.

Local Development Setup
================

- Create a virtualenv and install the requirements using pip install -r requirements.txt.
- Start gunicorn using ./run. By default the endpoints run on localhost:8000.
- You will need to set up the database locally. Easiest way to do this seems to be to do this in an interactive shell:
    ```
    from playhouse.sqlite_ext import SqliteExtDatabase
    db = SqliteExtDatabase('teapot.db')
    db.connect()
    from teabot_endpoints.models import PotMaker, State, SlackMessages
    db.create_tables([PotMaker, State, SlackMessages])
    ```
- You will then be able to test the endpoints using curl.

As there is no endpoint to add PotMakers, you can add them individually in a Python shell:

    PotMaker.create(name=‘Joe’, number_of_pots_made=0, total_weight_made=0, number_of_cups_made=0, largest_single_pot=0)
    
