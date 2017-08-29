from rest_framework.routers import SimpleRouter
from django.conf.urls import include, url

from .views import ProjectViewSet, CategoryViewSet

router = SimpleRouter()
router.register('projects', ProjectViewSet)


urlpatterns = [
        url(r'category/(?P<pk>[0-9]+)/$', CategoryViewSet.as_view({'get': 'retrieve',
                                                                   'patch': 'partial_update'}), name='category-detail'),
        url(r'^', include(router.urls)),
]