from django.core.exceptions import ObjectDoesNotExist
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from harvest.hooks import hookset as harvest_hookset
from teams.models import Team, Membership
from toggl.hooks import hookset as toggl_hookset

from .models import Category, Item, Project
from .serializers import CategorySerializer, ItemSerializer, ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    authentication_classes = (TokenAuthentication,)
    included = ['categories']
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    resource_name = 'projects'
    serializer_class = ProjectSerializer

    def perform_create(self, serializer):
        membership = Membership.objects.get(user_id=self.request.user.id)
        serializer.save(team=membership.team)

    def get_queryset(self):
        try:
            membership = Membership.objects.get(user_id=self.request.user.id)
            return membership.team.projects.all()
        except Membership.DoesNotExist:
            return []


class ProjectUpdateActualTimeView(GenericAPIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_api_key(self, user_profile):
        if user_profile.harvest_access_token:
            tokens = {
                'access_token': user_profile.harvest_access_token,
                'refresh_token': user_profile.harvest_refresh_token,
                'tokens_last_refreshed_at': user_profile.harvest_tokens_last_refreshed_at
            }
            return tokens, harvest_hookset
        elif user_profile.toggl_api_key:
            return user_profile.toggl_api_key, toggl_hookset
        else:
            return None, None

    def post(self, request, *args, **kwargs):
        project = self.get_object()

        try:
            user_profile = self.request.user.profile
            if not user_profile:
                raise ObjectDoesNotExist()
            api_key, hookset = self.get_api_key(user_profile)
            if not api_key:
                user_profile = project.team.creator.profile
                api_key, hookset = self.get_api_key(user_profile)
                if not api_key:
                    raise ObjectDoesNotExist()
        except ObjectDoesNotExist:
            raise ValidationError('Please login with Harvest or '
                                  'provide a Toggl API key.')

        project.update_actual(api_key, hookset)
        serializer = self.get_serializer(project)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet
                      ):
    included = ['items']
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Category.objects.all()
    resource_name = 'categories'
    serializer_class = CategorySerializer


class ItemViewSet(viewsets.ModelViewSet):
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Item.objects.all()
    resource_name = 'items'
    serializer_class = ItemSerializer
