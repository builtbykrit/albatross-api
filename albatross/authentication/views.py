from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_auth.views import LoginView as RestAuthLoginView


class LoginView(RestAuthLoginView):
    renderer_classes = (JSONRenderer,)
    parser_classes = (JSONParser,)