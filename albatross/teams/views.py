from albatross.invitations.serializers import InvitationSerializer

from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.response import Response

from .models import Membership, Team
from .serializers import TeamSerializer


class TeamListCreateView(ListCreateAPIView):
    included = ['memberships']
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Team.objects.all()
    resource_name = 'teams'
    serializer_class = TeamSerializer

    # def create(self, request, *args, **kwargs):
    #     serializer = self.get_serializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     self.perform_create(serializer)
    #
    #     team = serializer.instance
    #     team.memberships.get_or_create(
    #         user=team.creator,
    #         defaults={
    #             "role": Membership.ROLE_OWNER,
    #             "state": Membership.STATE_JOINED
    #         }
    #     )
    #     serializer = self.get_serializer(team)
    #
    #     headers = self.get_success_headers(serializer.data)
    #     return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class TeamInviteView(GenericAPIView):
    queryset = Team.objects.all()

    def post(self, request, format=None):
        team = self.get_object()
        serializer = InvitationSerializer(request.data)
        serializer.is_valid(raise_exception=True)

        team.invite_user(from_user=self.request.user,
                         to_email=serializer.validated_data['email'])

        # Add User to Team
        # Send Invitation
        return Response(status=status.HTTP_204_NO_CONTENT)



