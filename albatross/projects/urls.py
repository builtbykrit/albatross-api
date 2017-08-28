from rest_framework.routers import SimpleRouter

from .views import ProjectViewSet

router = SimpleRouter(trailing_slash=False)
router.register(r'', ProjectViewSet, 'projects')

urlpatterns = router.urls