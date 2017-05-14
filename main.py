#!/usr/bin/env python

import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb
import jinja2
import webapp2

from entities import Reservation
from entities import Resource
from entities import Tag
import helpers

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_RESERVATION_TABLE = "reservations"
DEFAULT_RESOURCE_TABLE = "resources"

def reservations_key(reservations_name=DEFAULT_RESERVATION_TABLE):
    return ndb.Key("Reservations", reservations_name)

def resources_key(resources_name=DEFAULT_RESOURCE_TABLE):
    return ndb.Key("Resources", resources_name)

# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            my_reservations = get_reservations(user)
            all_resources = get_resources()
            my_resources = [resource for resource in all_resources if resource.user == user]

            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
            template_values = {
                'user': user,
                'my_reservations' : my_reservations,
                'all_resources' : all_resources,
                'my_resources' : my_resources,
                'url': url,
                'url_linktext': url_linktext,
            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))
# [END main_page]

def get_reservations(user=None):
    reservations = list()
    if user:
        reservations = Reservation.query(
            Reservation.user == user,
            ancestor=reservations_key()
        ).order(Reservation.start_time).fetch()
    else:
        reservations = Reservation.query(
            ancestor=reservations_key()).order(Reservation.start_time).fetch()
    return reservations

def get_resources(user=None):
    resources = list()
    if user:
        resources = Resource.query(
            Resource.user == user,
            ancestor=resources_key()
        ).order(Resource.name).fetch()
    else:
        resources = Resource.query(
            ancestor=resources_key()
        ).order(-Resource.last_reservation_time).fetch()
    return resources

class Reservations(webapp2.RequestHandler):
    def post(self):
        reservation = Reservation(parent=reservations_key())
        resource = Resource.query(Resource.id == self.request.get('resource_id')).fetch(1)

        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
        else:
            if not resource:
                print("lol")
            else:
                reservation.user = users.get_current_user()
                reservation.resource_id = self.request.get('resource_id')
                reservation.start_time = self.request.get('start_time')
                reservation.duration = self.request.get('duration')
                reservation.put()
                query_params = {'reservations_name' : DEFAULT_RESERVATION_TABLE}
                self.redirect('/')

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/make-reservation', Reservations),
], debug=True)

