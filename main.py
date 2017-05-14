#!/usr/bin/env python

import os
import uuid
from datetime import datetime

from google.appengine.api import users
from google.appengine.ext import ndb
import jinja2
import webapp2

from entities import Reservation
from entities import Resource
from entities import Tag
import PyRSS2Gen

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_RESERVATION_TABLE = "reservations"
DEFAULT_RESOURCE_TABLE = "resources"

def to_RSS(resource):
    rss = PyRSS2Gen.RSS2(
        title = resource.name,
        link = "resource?rssid=" + str(resource.id),
        description = "RSS feed for resource " + resource.name,
        lastBuildDate = datetime.utcnow(),

        items = [
            PyRSS2Gen.RSSItem(
                title = reservation.user_id,
                link = "/reservation?id=" + str(reservation.user_id),
                description = "user " + reservation.user_id + "'s reservation",
                guid = PyRSS2Gen.Guid(str(uuid.uuid1())),
                pubDate = datetime.utcnow())
        for reservation in resource.reservations ])
    return rss.to_xml()

def reservations_key(reservations_name=DEFAULT_RESERVATION_TABLE):
    return ndb.Key("Reservations", reservations_name)

def resources_key(resources_name=DEFAULT_RESOURCE_TABLE):
    return ndb.Key("Resources", resources_name)

def get_reservations_by_user(user=None):
    reservations = list()
    if user:
        reservations = Reservation.query(
            Reservation.user_id == str(user.user_id()),
            Reservation.start_time >= datetime.now().time(),
            ancestor=reservations_key()
        ).order(Reservation.start_time).fetch()
        if len(reservations) >= 1:
            return reservations
    return []

def get_resources(user=None):
    resources = list()
    if user:
        resources = Resource.query(
            Resource.user_id == str(user.user_id()),
            ancestor=resources_key()
        ).order(Resource.name).fetch()
    else:
        resources = Resource.query(
            ancestor=resources_key()
        ).order(-Resource.last_reservation_time).fetch()
    return resources

def get_resource_by_id(id=None):
    if id:
        resource_fetch = Resource.query(
            Resource.id == id
        ).fetch()
        if len(resource_fetch) >= 1:
            return resource_fetch
    return []

def get_end_time(reservation):
    return ((datetime.combine(datetime.min, reservation.start_time)) +\
           (datetime.combine(datetime.min, reservation.duration) - datetime.min)).time()

def valid_reservation_time(start_time_new, end_time_new, start_time_old, end_time_old):
    valid = True
    if start_time_new >= start_time_old and start_time_new <= end_time_old:
        valid = False
    elif end_time_new >= start_time_old and end_time_new <= end_time_old:
        valid = False
    return valid

class MainPage(webapp2.RequestHandler):

    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            my_reservations = get_reservations_by_user(user)
            all_resources = get_resources()
            my_resources = [resource for resource in all_resources if resource.user_id == str(user.user_id())]

            url = users.create_logout_url(self.request.uri)
            template_values = {
                'user': user,
                'my_reservations' : my_reservations,
                'all_resources' : all_resources,
                'my_resources' : my_resources,
                'url': url,
            }

            template = JINJA_ENVIRONMENT.get_template('index.html')
            self.response.write(template.render(template_values))

class Reservations(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('id', None)
        if id:
            reservation = Reservation.query(
                Reservation.id == id,
                ancestor=reservations_key()
            ).fetch(1)
            if len(reservation) < 1:
                self.redirect('/')
            if self.request.get('delete') == '1':
                resource = get_resource_by_id(reservation[0].resource_id)
                resource[0].key.delete()
                reservation[0].key.delete()
                self.redirect('/')
        else:
            self.redirect('/')

    def post(self):
        reservation = Reservation(parent=reservations_key())
        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
        else:
            resource = get_resource_by_id(self.request.get('resource_id'))
            if len(resource) < 1:
                self.redirect('/')
            else:
                reservation.id = str(uuid.uuid1())
                reservation.user_id = str(users.get_current_user().user_id())
                reservation.resource_id = resource[0].id
                reservation.resource_name = resource[0].name
                reservation.start_time = datetime.strptime(self.request.get('start_time'),'%H:%M:%S').time()
                reservation.duration = datetime.strptime(self.request.get('duration'),'%H:%M:%S').time()
                end_time = get_end_time(reservation)
                if reservation.start_time < resource[0].start_time or end_time > resource[0].end_time:
                    template = JINJA_ENVIRONMENT.get_template('status.html')
                    template_values = {
                        'status' : "Failed. Resource not available during the selected time.",
                        'return_url' : self.request.uri
                    }
                    self.response.write(template.render(template_values))
                    return
                for res in resource[0].reservations:
                    res_end_time = get_end_time(res)
                    if not valid_reservation_time(reservation.start_time, end_time, res.start_time, res_end_time):
                        template = JINJA_ENVIRONMENT.get_template('status.html')
                        template_values = {
                            'status' : "Failed. Others using the resource during the selected time.",
                            'return_url' : self.request.uri
                        }
                        self.response.write(template.render(template_values))
                        return
                reservation.put()
                resource[0].reservations.append(reservation)
                resource[0].last_reservation_time = datetime.now().time()
                resource[0].put()
                template = JINJA_ENVIRONMENT.get_template('status.html')
                template_values = {
                    'status' : "Success.",
                    'return_url' : self.request.uri,
                }
                self.response.write(template.render(template_values))
                query_params = {'reservations_name' : DEFAULT_RESERVATION_TABLE}

class CreateReservation(webapp2.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
        else:
            resource = get_resource_by_id(self.request.get('id'))
            if len(resource) < 1:
                self.redirect('/')
            else:
                template = JINJA_ENVIRONMENT.get_template('create-reservation.html')
                template_values = {
                    'resource' : resource[0]
                }
                self.response.write(template.render(template_values))

class CreateResource(webapp2.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
        else:
            template = JINJA_ENVIRONMENT.get_template('edit-resource.html')
            if self.request.get('type') == 'create':
                resource = Resource()
                resource.name = "name"
                resource.start_time = datetime.min.time()
                resource.end_time = datetime.max.time()
                template_values = {
                    'resource' : resource,
                    'start_time' : str(resource.start_time)[0:8],
                    'end_time' : str(resource.end_time)[0:8],
                    'edit' : False,
                    'tags' : ""
                }
                self.response.write(template.render(template_values))
            elif self.request.get('type') == 'edit':
                resource = get_resource_by_id(self.request.get('id'))
                if len(resource) < 1:
                    self.redirect('/')
                else:
                    tags = ""
                    for tag in resource[0].tags:
                        tags += tag.name
                        tags += " "
                    template_values = {
                        'resource' : resource[0],
                        'start_time' : str(resource.start_time)[0:8],
                        'end_time' : str(resource.end_time)[0:8],
                        'tags' : tags,
                        'edit' : True
                    }
                    self.response.write(template.render(template_values))
            else:
                self.redirect('/')

    def post(self):
        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
        elif not self.request.get('name'):
            self.redirect('/')
        else:
            id = self.request.get('resource_id')
            resource_fetch = get_resource_by_id(id)
            resource = Resource(parent=resources_key())
            if id and len(resource_fetch) > 0:
                resource = resource_fetch[0]
            resource.id = str(uuid.uuid1()) if not id else id
            resource.user_id = str(users.get_current_user().user_id())
            resource.name = self.request.get('name')
            resource.start_time = datetime.strptime(self.request.get('start_time', '00:00'),'%H:%M:%S').time()
            resource.end_time = datetime.strptime(self.request.get('end_time', '23:59'),'%H:%M:%S').time()
            if resource.start_time >= resource.end_time:
                template = JINJA_ENVIRONMENT.get_template("status.html")
                template_values = {
                    'status' : "Failed. Invalid time."
                }
                self.response.write(template.render(template_values))
                return
            taglist = []
            if self.request.get('tags'):
                tagsstr = self.request.get('tags')
                tags = tagsstr.split()
                for tagstr in tags:
                    tag = Tag()
                    tag.id = str(uuid.uuid1())
                    tag.name = tagstr
                    taglist.append(tag)
            resource.tags = taglist
            # only put into the database if the availability is valid
            resource.put()
            template_values = {
                'status' : "Success."
            }
            template = JINJA_ENVIRONMENT.get_template("status.html")
            self.response.write(template.render(template_values))

class ResourceDetail(webapp2.RequestHandler):
    def get(self):
        if not users.get_current_user():
            self.redirect(users.create_login_url(self.request.uri))
        else:
            resource = get_resource_by_id(self.request.get('id'))
            if len(resource) < 1:
                self.redirect('/')
            else:
                if self.request.get('rss') == '1':
                    self.response.write(to_RSS(resource[0]))
                    return
                can_edit = str(users.get_current_user().user_id()) == resource[0].user_id
                # reservations = []
                # for reservation_id in resource.reservation_ids:
                #     reservation = Reservation.query(Reservation.id == reservation_id).fetch(1)
                #     if reservation:
                #         reservations.append(reservation)
                template_values = {
                    'resource' : resource[0],
                    # 'reservations' : reservations,
                    'can_edit' : can_edit
                }
                template = JINJA_ENVIRONMENT.get_template('resource.html')
                self.response.write(template.render(template_values))
class UserDetail(webapp2.RequestHandler):
    def get(self):
        id = self.request.get('id')
        if not id:
            self.redirect('/')
        else:
            resources = Resource.query(
                Resource.user_id == id
            ).fetch()
            reservations = Reservation.query(
                Reservation.user_id == id
            ).fetch()
            template_values = {
                'id' : id,
                'my_resources' : resources,
                'my_reservations' : reservations
            }
            template = JINJA_ENVIRONMENT.get_template('user.html')
            self.response.write(template.render(template_values))

def clean():
    for resource in get_resources():
        resource.key.delete()
    for reservation in Reservation.query().fetch():
        reservation.key.delete()
# clean()
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/reservation', Reservations),
    ('/create-reservation', CreateReservation),
    ('/resource', ResourceDetail),
    ('/edit-resource', CreateResource),
    ('/user', UserDetail)
], debug=True)

