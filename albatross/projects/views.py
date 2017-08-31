from rest_framework import viewsets, mixins, permissions
from rest_framework.authentication import TokenAuthentication
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

