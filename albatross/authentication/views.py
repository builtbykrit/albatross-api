from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework_json_api.parsers import JSONParser as JSONAPIParser
from rest_framework_json_api.renderers import JSONRenderer as JSONAPIRenderer
from rest_auth.views import LoginView as RestAuthLoginView
from rest_auth.views import UserDetailsView as RestAuthUserView


class LoginView(RestAuthLoginView):
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)


class UserView(RestAuthUserView):
    renderer_classes = (JSONAPIRenderer,)
    parser_classes = (JSONAPIParser,)
