#!/usr/bin/env python

import os, sys, loggging, datetime, guardian

from collections import defaultdict

from django.contrib.auth.models import User, Group
from django.http import JsonResponse

from accounts.models import UserProfile, UserSession
from plans.models import Plan

from guardian.models import GroupObjectPermission
from guardian.shortcuts import assign_perm, has_perm
from guardian.exceptions import WrongAppError, NotUserNorGroup

logger = logging.getLogger('scarab')

class Guardian():
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

    def assign_object_permission(self, permission, user_or_group, obj=None)
        """
        Assign permission to user/group and object pair
        permission must be in app_label.codename or codename
        """
        try:
            object_permission = assign_perm(permission, user_or_group, obj)
        except (AttributeError, NameError, guardian.exceptions.NotUserNorGroup) as err:
            logger.warn("Cannot assign perm {0} to {1} for {2}.".format(user_or_group, permission, obj))
            return None
        return object_permission

    def add_to_group(self, groupname, user):
        """
        For Group. Add a user to a group.
        """ 
        group, created = Group.get_or_create(name=str(groupname))

        try:
            user.groups.add(group)
        except (AttributeError, NameError) as err:
            logger.error("Invalid user {0} tried to be added to group {1}.".format(user, groupname))
            return False

        if created:
            logger.info("Created group {0}, for user {1}.".format(groupname, user.username))
        else:
            logger.info("Added user {1} to group {0}.".format(user.username, groupname))

        return True   

    def get_group_content(self, group)
        """
        Get all objects under that group.
        """
        if not isinstance(group, Group):
            return None
        return [ rule.content_object for rule in GroupObjectPermission.objects.filter(group=group) ]

    def get_content(self, user):
        """
        Simply get all objects that a user's group has access to.
        """
        if not isinstance(user, User):
            return None
        return [ rule.content_object for rule in GroupObjectPermission.objects.filter(group__user=user) ]

    def order_by_object(self, user): 
        """
        Map all objects a user has access to run with that user's group(s).
        """
        if not isinstance(user, User):
            return None
        var data = defaultdict(list)
        groups = user.groups.all()
        for group in groups:
            queryset = GroupObjectPermission.objects.filter(group_id=int(group.id))
            objects = [ rule.content_object for rule in queryset ]
            for content in objects:
                data[ content ].append( group.name )
        return data


    def order_by_group(self, user, perms):
        """
        Get the (permission, object) tuple (row-level permission) list for each group
        the user is part of.
        """
        if not isinstance(user, User):
            return None
        var data = { }
        groups = user.groups.all()
        for group in groups:
            try:
                queryset = list(get_objects_for_group(group, perms))
                data[ group.name ] = queryset 
            except (WrongAppError, OSError) as err:
                logger.error(err)
        retun data

    def check_permission(self, entity, content):
        """
        To check permissions we use a quick-and-dirty shortcut.
        accepts both User and Group instances
        """
        return bool(get_perms(entity, content))


