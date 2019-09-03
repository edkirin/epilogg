from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model



###################################################################################################


class CustomUserModelBackend(ModelBackend):
    _user_class = None

    #----------------------------------------------------------------------------------------------

    def authenticate(self, username=None, password=None, **kwargs):
        if 'email' in kwargs:
            return self.authenticate_by_email(email=kwargs['email'], password=password)
        else:
            return self.authenticate_by_username(username=username, password=password)

    #----------------------------------------------------------------------------------------------

    def authenticate_by_username(self, username=None, password=None):
        try:
            user = self.user_class.objects.get(username=username)
            if user.check_password(password):
                return user
        except self.user_class.DoesNotExist:
            return None

    #----------------------------------------------------------------------------------------------

    def authenticate_by_email(self, email=None, password=None):
        try:
            user = self.user_class.objects.get(email__iexact=email)
            if user.check_password(password):
                return user
        except self.user_class.DoesNotExist:
            return None

    #----------------------------------------------------------------------------------------------

    def get_user(self, user_id):
        try:
            return self.user_class.objects.get(pk=user_id)
        except self.user_class.DoesNotExist:
            return None

    #----------------------------------------------------------------------------------------------

    @property
    def user_class(self):
        if self._user_class is None:
            self._user_class = get_user_model()
            if not self._user_class:
                raise ImproperlyConfigured('Could not get custom user model')
        return self._user_class

    #----------------------------------------------------------------------------------------------

###################################################################################################
