from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.http import HttpRequest

from webscanner.logger import logger

import sys, os
# Create your models here.
class UserProfile(models.Model):
    user      = models.OneToOneField(User, unique=True)
    date      = models.DateTimeField(auto_now_add=True)
    biography = models.TextField(default='', blank=True) 
 
    def __unicode__(self):
        return 'User Profile for: ' + self.user.username

    def get_latest_session(self):
        user_sessions = UserSession.objects.filter(user = self.user)
        return user_sessions[len(user_sessions)-1]
        
def create_profile(sender, **kwargs):
    """
    Automatically creating a UserProfile object whenever a
    User object is created.
    """
    user = kwargs["instance"]
    if kwargs["created"]:
        user_profile = UserProfile.objects.create(user=user)

post_save.connect(create_profile, sender=User)

class UserSession(models.Model):
    """
    Create a database model to link a User to a Session
    Only concerned with logged in user sessions.
    """
    user    = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user")
    session = models.ForeignKey(Session, on_delete=models.CASCADE, null=True)

    def delete_user_session(self):
        user_sessions = UserSessions.objects.filter(user = self.user)
        for user_session in user_sessions:
            user_sessions.session.delete()

    def set_session(self, task_function, **kwargs):
        session_dictionary = self.session.get_decoded()    
        for key, value in kwargs.iteritems():
            task_function(session_dictionary, key, value)
        self.session.session_data = Session.objects.encode(session_dictionary)
        self.session.save()
        logger.info(session_dictionary)

    def getitem(self, key):
        try:
            item = self.session.get_decoded()[key]
        except KeyError as nonexistant:
            return None
        else: 
            return item

    def setitem(self, session_dictionary, key, value):
        session_dictionary[key] = value

    def appenditem(self, session_dictionary, key, value):
        if not key in session_dictionary or not type(session_dictionary[key]) is list:
            session_dictionary[key] = list()
        session_dictionary[key].append(value) 

    def delitem(self, session_dictionary, key):
        try:
            del session_dictionary[key]
        except KeyError as nonexistant:
            return None

    def unappenditem(self, session_dictionary, key, value):
        try:
            session_dictionary[key].remove(value)
        except (KeyError, ValueError) as e:
            return None

        
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Save an instance of this mapping model every time a 
    user logs in, through the user of Django's user_logged_in signal
    """
    UserSession.objects.get_or_create(
        user       = user,
        session_id = request.session.session_key
    )

user_logged_in.connect(user_logged_in_handler)

