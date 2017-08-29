from rest_framework import viewsets
from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    pagination_class = None
    serializer_class = ProjectSerializer
    resource_name = 'projects'
