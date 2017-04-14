#!/usr/bin/env python

import os, sys, logging, datetime, guardian

from collections import defaultdict

from django.contrib.auth.models import User, Group, ContentType
from django.http import JsonResponse

from accounts.models import UserProfile, UserSession
from plans.models import Plan

from guardian.models import GroupObjectPermission
from guardian.shortcuts import assign_perm, get_perms, remove_perm
from guardian.exceptions import WrongAppError, NotUserNorGroup

logger = logging.getLogger('scarab')

class Guardian():
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)

    def assign_object_permission(self, permission, user_or_group, obj):
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
        group, created = Group.objects.get_or_create(name=str(groupname))

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

    def get_group_content(self, group):
        """
        Get all objects under that group.
        """
        if not isinstance(group, Group):
            return None
        return [ rule.content_object for rule in GroupObjectPermission.objects.filter(group=group) ]

    def get_user_content(self, user):
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
        data = defaultdict(list)
        groups = user.groups.all()
        for group in groups:
            queryset = GroupObjectPermission.objects.filter(group_id=int(group.id))
            objects = [ rule.content_object for rule in queryset ]
            for content in objects:
                data[ content ].append( group )
        return data

    def __get_objects_for_group(self, group):
        try:
            queryset = GroupObjectPermission.objects.filter(group=group)
        except (ValueError, WrongAppError, OSError) as err:
            logger.error(err)
            return None
        return queryset

    def order_by_group(self, user):
        """
        Get the (permission, object) tuple (row-level permission) list for each group
        the user is part of.
        """
        if not isinstance(user, User):
            return None
        data = { }
        groups = user.groups.all()
        for group in groups:
            data[ group ] = self.__get_objects_for_group(group)
        return data

    def check_permission(self, entity, content):
        """
        To check permissions we use a quick-and-dirty shortcut.
        accepts both User and Group instances
        """
        return bool(get_perms(entity, content))
   
    def leave_group(self, name, user):
        try:
            group = Group.objects.get(name=name)
            group.user_set.remove(user)
        except (ValueError, Group.DoesNotExist) as err:
            logger.error("Invalid Group/User {0}.".format(err))
            return False
        return True

    def revoke_permision(self, entity, content):
        """
        Removes permission from user/group and object pair.
        """
        try: 
            permissions = get_perms(entity, content)
            for permission in permissions:
                remove_perm(permission, entity, obj=content)
        except NotUserNorGroup as err:
            logger.error("Invalid Operation: {0}.".format(err))
            return False
        return True

    def verify_by_contenttype(self, model, entity, content_primary_key):
        """
        Uses the content type to get the object with its primary key and
        verify that entity has access to it.
        """
        try:
            model_type = ContentType.objects.get(model=model)
            content = ContentType.get_object_for_this_type(model_type, pk=content_primary_key)
        except (ContentType.DoesNotExist, Plan.DoesNotExist, TypeError) as err:
            logger.error(err)
            return None

        authorization = self.check_permission(entity, content)
        return content if authorization else None
