from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework_json_api.parsers import JSONParser as JSONAPIParser
from rest_framework_json_api.renderers import JSONRenderer as JSONAPIRenderer
from rest_auth.views import LoginView as RestAuthLoginView
from rest_auth.views import LogoutView as RestAuthLogoutView
from rest_auth.views import PasswordChangeView as RestAuthPasswordChangeView
from rest_auth.views import PasswordResetConfirmView as \
    RestAuthPasswordResetConfirmationView
from rest_auth.views import PasswordResetView as RestAuthPasswordResetView
from rest_auth.views import UserDetailsView as RestAuthUserView

from .serializers import UserSerializer


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
