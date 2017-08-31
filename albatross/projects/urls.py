from rest_framework.routers import SimpleRouter
from django.conf.urls import include, url

from .views import CategoryViewSet, ItemViewSet, ProjectViewSet

router = SimpleRouter()
router.register(r'^projects/$', ProjectViewSet, 'project')
router.register(r'^categories/$', CategoryViewSet)
router.register(r'^items/$', ItemViewSet)


urlpatterns = router.urls