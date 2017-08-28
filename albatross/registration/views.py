from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from rest_framework.exceptions import APIException,ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework_json_api import renderers

from .serializers import UserRegistrationSerializer


class UserRegistrationView(CreateAPIView):
    model = User
    renderer_classes = (renderers.JSONRenderer,)
    resource_name = 'users'
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except IntegrityError as e:
            strE = str(e)
            if 'Key (username)=(' in strE and ') already exists.' in strE:
                raise ValidationError(
                    'Another user is already registered using that email.'
                )
            else:
                raise APIException(strE)