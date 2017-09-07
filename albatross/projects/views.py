from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser
from .models import Category, Item, Project
from .serializers import CategorySerializer, ItemSerializer, ProjectSerializer
from teams.models import Team, Membership

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

    def post(self, request, *args, **kwargs):
        project = self.get_object()
        project.update_actual()
        serializer = self.get_serializer(project)
        return Response(serializer.data)


class CategoryViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet
                      ):
    included = ['items']
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Category.objects.all()
    resource_name = 'categories'
    serializer_class = CategorySerializer



class ItemViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet
                  ):
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Item.objects.all()
    resource_name = 'items'
    serializer_class = ItemSerializer

