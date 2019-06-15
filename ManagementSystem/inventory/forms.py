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


class LoginForm(forms.Form):
    email_id = forms.CharField(widget=forms.EmailInput, required=True, label="Email ID")
    password = forms.CharField(widget=forms.PasswordInput, required=True, max_length=32, label="Password")
