from rest_framework.routers import SimpleRouter
from django.conf.urls import include, url

from .views import (
    CategoryViewSet,
    ItemViewSet,
    ProjectViewSet,
    ProjectUpdateActualTimeView
)

router = SimpleRouter()
router.register(r'projects', ProjectViewSet, 'project')
router.register(r'categories', CategoryViewSet)
router.register(r'items', ItemViewSet)

project_update_actual_time_url = url(
    r"^projects/(?P<pk>[0-9]+)/update-actual-time/$",
    ProjectUpdateActualTimeView.as_view(),
    name="project-update-actual-time"
)

urlpatterns = router.urls
urlpatterns.insert(0, project_update_actual_time_url)