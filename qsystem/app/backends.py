#app/backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

class UsernameOnlyBackend(BaseBackend):
    def authenticate(self, request, username=None, **kwargs):
        try:
            user = User.objects.get(username=username)
            # Return the user object if found
            return user
        except ObjectDoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except ObjectDoesNotExist:
            return None
