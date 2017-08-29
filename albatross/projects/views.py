from rest_framework import viewsets, mixins
from .models import Category, Item, Project
from .serializers import CategorySerializer, ItemSerializer, ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    pagination_class = None
    serializer_class = ProjectSerializer
    resource_name = 'projects'
    included = ['categories']


class CategoryViewSet(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      viewsets.GenericViewSet
                      ):
    queryset = Category.objects.all()
    pagination_class = None
    serializer_class = CategorySerializer
    resource_name = 'categories'
    included = ['items']


class ItemViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet
                  ):
    queryset = Item.objects.all()
    pagination_class = None
    serializer_class = ItemSerializer
    resource_name = 'items'
