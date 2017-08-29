from rest_framework.routers import SimpleRouter

from .views import ProjectViewSet

router = SimpleRouter()
router.register('projects', ProjectViewSet)

urlpatterns = router.urls