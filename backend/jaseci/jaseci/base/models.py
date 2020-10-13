import uuid
from datetime import datetime

from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, \
    PermissionsMixin
from base.orm_hook import orm_hook
from core import master


class UserManager(BaseUserManager):
    """
    Custom User Manager for Jaseci

    Note: Every user is linked to a single root node that is created upon the
    creation of the user.
    """

    def create_user(self, email, password=None, **extra_fields):
        """Creates and saves a new user"""
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        # Create user's root node
        user.master = master.master(h=user._h,
                                    email=self.normalize_email(email)).id
        user._h.commit()

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Creates and saves a new super user"""
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.is_staff = True
        user.is_admin = True
        user.is_superuser = True
        user.save(using=self._db)

        # Create user's root node
        user.master = master.master(h=user._h,
                                    email=self.normalize_email(email)).id
        user._h.commit()

        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model to use email instead of username

    Root node  is attached to each User and created at user creation
    """
    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    time_created = models.DateTimeField(auto_now_add=True)
    time_modified = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    master = models.UUIDField(default=uuid.uuid4)
    objects = UserManager()

    def __init__(self, *args, **kwargs):
        self._h = orm_hook(
            user=self, objects=JaseciObject.objects
        )
        AbstractBaseUser.__init__(self, *args, **kwargs)
        PermissionsMixin.__init__(self, *args, **kwargs)

    USERNAME_FIELD = 'email'

    def get_master(self):
        """Returns main user Jaseci node"""
        return self._h.get_obj(self.master)


class JaseciObject(models.Model):
    """
    Generalized object model for Jaseci object types

    There is one table in db for all object types in the Jaseci machine
    which include nodes, edges, actions, contexts, walkers, and
    sentinels.

    Keep in mind Django's ORM can support many to many relationships
    between recursive schema's which may be useful if necessary in the
    future.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, editable=False,
                             on_delete=models.CASCADE)
    jid = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False)
    j_owner = models.UUIDField(null=True, blank=True)
    name = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=255, blank=True)
    j_timestamp = models.DateTimeField(default=datetime.utcnow)

    # j_type keeps track of the type of the object
    j_type = models.CharField(max_length=15, default='node')
    # jsci_obj is json dump of entire object data beyond base
    jsci_obj = models.TextField(blank=True)