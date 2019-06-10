from django.urls import path
from .views import inventory, approvals


urlpatterns = [
    path('inventory', inventory, name='inventory'),
    path('approvals', approvals, name='approvals')
]