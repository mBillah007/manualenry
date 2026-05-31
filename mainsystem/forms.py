from django import forms
from mainsystem.models import CustomUser, Role, Permission, Module

class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'is_protected']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'রোল নাম'}),
            'is_protected': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class DashboardForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}), required=False)
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError("Start date cannot be after end date.")
        return cleaned_data
class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = [
            'name', 'label', 'url_name', 'icon', 'order',
            'parent', 'group', 
            'is_visible', 'is_header'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Module Name'}),
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Module Label'}),
            'url_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'URL Name'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Icon Class'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Order'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_header': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }