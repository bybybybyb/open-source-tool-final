from google.appengine.ext import ndb
from datetime import  time

class Tag(ndb.Model):
    id = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)

class Reservation(ndb.Model):
    id = ndb.StringProperty(indexed=True)
    resource_id = ndb.StringProperty(indexed=True)
    resource_name = ndb.StringProperty(indexed=False)
    start_time = ndb.TimeProperty(indexed=True)
    duration = ndb.TimeProperty(indexed=True)
    user_id = ndb.StringProperty(indexed=True)

class Resource(ndb.Model):
    id = ndb.StringProperty(indexed=True)
    user_id = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)
    start_time = ndb.TimeProperty(default=time.min, indexed=True)
    end_time = ndb.TimeProperty(default=time.max, indexed=True)
    tags = ndb.StructuredProperty(Tag, repeated=True)
    last_reservation_time = ndb.TimeProperty(indexed=True)
    reservations = ndb.StructuredProperty(Reservation, repeated=True)

