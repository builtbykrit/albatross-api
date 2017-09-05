from django.shortcuts import render
from rest_framework import permissions
from rest_framework.generics import RetrieveAPIView
from .models import Invitation
from .serializers import InvitationSerializer
# Create your views here.
class InvitationDetailView(RetrieveAPIView):
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer