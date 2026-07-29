from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import HistoricalProjectViewSet, rebuild_index, search_index

router = DefaultRouter()
router.register(r'historical-projects', HistoricalProjectViewSet, basename='historical-project')

urlpatterns = [
    path('rebuild-index/', rebuild_index, name='rebuild-index'),
    path('search-index/', search_index, name='search-index'),
] + router.urls