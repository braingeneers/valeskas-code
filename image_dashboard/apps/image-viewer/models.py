"""
This file defines the database models
"""

import datetime
from .common import db, Field, auth
from pydal.validators import *


def get_user_email():
    return auth.current_user.get('email') if auth.current_user else None

def get_time():
    return datetime.datetime.utcnow()


### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later

db.define_table(
    "experiments",
    Field("experiment_name", default=[]),
    auth.signature
)

db.define_table(
    "cam_names",
    Field("cam_name", default=[]),
    Field("experiment_id", "reference experiments"),
    auth.signature
)

db.commit()
