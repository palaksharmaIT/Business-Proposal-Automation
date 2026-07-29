from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import ProposalViewSet, generate_proposal

router = DefaultRouter()
router.register(r'proposals', ProposalViewSet, basename='proposal')

urlpatterns = [
    path('generate/', generate_proposal, name='generate-proposal'),
] + router.urls