from django.urls import path
from .views import inventory, approvals, login, logout, inventoryitem


urlpatterns = [
    path('inventory', inventory, name='inventory'),
    path('approvals', approvals, name='approvals'),
    path('inventoryitem/<str:operation>', inventoryitem, name='inventoryitem'),
    path('inventoryitem/<str:operation>/<str:product_id>', inventoryitem, name='inventoryitemedit'),
    path('login', login, name='login'),
]