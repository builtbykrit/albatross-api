import json

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from rest_auth.views import LoginView as RestAuthLoginView
from rest_auth.views import LogoutView as RestAuthLogoutView
from rest_auth.views import PasswordChangeView as RestAuthPasswordChangeView
from rest_auth.views import PasswordResetConfirmView as \
    RestAuthPasswordResetConfirmationView
from rest_auth.views import PasswordResetView as RestAuthPasswordResetView
from rest_auth.views import UserDetailsView as RestAuthUserView
from rest_framework import permissions
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, UpdateAPIView, GenericAPIView
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_json_api.parsers import JSONParser as JSONAPIParser
from rest_framework_json_api.renderers import JSONRenderer as JSONAPIRenderer

from .models import UserProfile
from .serializers import ProfileSerializer, UserSerializer, HarvestSerializer


class LoginView(RestAuthLoginView):
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)


class LogoutView(RestAuthLogoutView):
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)


class PasswordChangeView(RestAuthPasswordChangeView):
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)


class PasswordResetConfirmationView(RestAuthPasswordResetConfirmationView):
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)


class PasswordResetView(RestAuthPasswordResetView):
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)


class UserView(RestAuthUserView):
    renderer_classes = (JSONAPIRenderer,)
    parser_classes = (JSONAPIParser,)
    serializer_class = UserSerializer


class UserDetailView(RetrieveAPIView):
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserProfileView(UpdateAPIView):
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer

class UserProfileHarvestView(GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)
    serializer_class = HarvestSerializer

    def get_tokens(self, authorization_code):
        print(settings.HARVEST_CLIENT_ID)
        print(settings.HARVEST_CLIENT_SECRET)
        body = 'code={authorization_code}&client_id={client_id}&client_secret={client_secret}&grant_type=authorization_code'.format(
            authorization_code=authorization_code, client_id=settings.HARVEST_CLIENT_ID,
            client_secret=settings.HARVEST_CLIENT_SECRET
        )
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
        resp = requests.post('https://id.getharvest.com/api/v1/oauth2/token', headers=headers, data=body, verify=False)
        if resp.status_code >= 400:
            raise ValidationError("Failed to retrieve Harvest tokens")
        return json.loads(resp.content.decode())

    def post(self, request, *args, **kwargs):
        profile = self.request.user.profile

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        authorization_code = serializer.validated_data['authorization_code']
        json_response = self.get_tokens(authorization_code)

        harvest_access_token = json_response["access_token"]
        harvest_refresh_token = json_response["refresh_token"]

        print(harvest_access_token)
        print(profile)

        profile.harvest_access_token = harvest_access_token
        profile.harvest_refresh_token = harvest_refresh_token
        profile.save()

        return Response(status=status.HTTP_204_NO_CONTENT)






