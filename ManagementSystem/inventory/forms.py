from django import forms
from .models import Inventory


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['product_id', 'product_name', 'vendor', 'mrp', 'batch_num','batch_date','quantity']
