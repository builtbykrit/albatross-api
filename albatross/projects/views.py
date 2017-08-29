from rest_framework import viewsets, mixins
from .models import Project, Category
from .serializers import CategorySerializer, ProjectSerializer


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
