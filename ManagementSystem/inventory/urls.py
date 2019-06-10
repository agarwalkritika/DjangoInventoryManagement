from django.urls import path
from .views import inventory, approvals, login, logout


urlpatterns = [
    path('inventory', inventory, name='inventory'),
    path('approvals', approvals, name='approvals'),
    path('login', login, name='login')
]