from rest_framework import viewsets, mixins, permissions
from .models import Category, Item, Project
from .serializers import CategorySerializer, ItemSerializer, ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    included = ['categories']
    pagination_class = None
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Project.objects.all()
    resource_name = 'projects'
    serializer_class = ProjectSerializer



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

