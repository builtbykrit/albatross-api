from invitations.serializers import InvitationCreateSerializer

from rest_framework import parsers, permissions, status
from rest_framework.generics import CreateAPIView, \
    GenericAPIView, RetrieveAPIView
from rest_framework.response import Response

from .models import Team
from .serializers import TeamSerializer


class TeamCreateView(CreateAPIView):
    included = ['memberships']
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Team.objects.all()
    resource_name = 'teams'
    serializer_class = TeamSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['user'] = self.request.user
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TeamInviteView(GenericAPIView):
    parser_classes = (parsers.JSONParser,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Team.objects.all()
    serializer_class = InvitationCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = InvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = self.get_object()
        team.invite_user(from_user=self.request.user,
                         to_email=serializer.validated_data['email'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamRetrieveView(RetrieveAPIView):
    included = ['memberships']
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Team.objects.all()
    resource_name = 'teams'
    serializer_class = TeamSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
