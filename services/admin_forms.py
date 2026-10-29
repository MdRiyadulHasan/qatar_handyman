from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import Category, Service


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = "__all__"
        widgets = {"description": CKEditor5Widget(config_name="default")}


class ServiceAdminForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = "__all__"
        widgets = {"description": CKEditor5Widget(config_name="default")}
