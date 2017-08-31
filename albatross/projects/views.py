from rest_framework import viewsets, mixins, permissions
from .models import Category, Item, Project
from .serializers import CategorySerializer, ItemSerializer, ProjectSerializer
from teams.models import Team

class ProjectViewSet(viewsets.ModelViewSet):
    included = ['categories']
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    resource_name = 'projects'
    serializer_class = ProjectSerializer

    def perform_create(self, serializer):
        team = Team.objects.get(creator=self.request.user)
        serializer.save(team=team)

    def get_queryset(self):
        team = Team.objects.get(creator=self.request.user)
        return team.projects.all()


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

