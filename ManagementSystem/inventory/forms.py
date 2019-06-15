from django import forms
from .models import Inventory


class InventoryModelForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['product_id', 'product_name', 'vendor', 'mrp', 'batch_num', 'batch_date', 'quantity']
        widgets = {
            'batch_date' : forms.SelectDateWidget()
        }


class InventoryForm(forms.Form):
    product_id = forms.CharField(max_length=10)
    product_name = forms.CharField(max_length=32)
    vendor = forms.CharField(max_length=32)
    mrp = forms.FloatField()
    batch_num = forms.CharField(max_length=32)
    batch_date = forms.DateField(widget=forms.SelectDateWidget())
    quantity = forms.IntegerField()
