from rest_framework.routers import SimpleRouter
from django.conf.urls import include, url

from .views import CategoryViewSet, ItemViewSet, ProjectViewSet

router = SimpleRouter()
router.register('projects', ProjectViewSet)
router.register('categories', CategoryViewSet)
router.register('items', ItemViewSet)


urlpatterns = router.urls