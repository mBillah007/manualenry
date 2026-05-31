from django import apps
from django import forms
from hrm.models import Profile, Role, Department, LeaveRequest, PublicHoliday


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ['user']  # ✅ Prevents Django from expecting it in form
        fields = '__all__'
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'নামের প্রথম অংশ',
                'autocomplete': 'given-name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'নামের শেষ অংশ',
                'autocomplete': 'family-name'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control form-control-sm',
                'type': 'date',
                'placeholder': 'জন্ম তারিখ'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'ফোন নম্বর',
                'inputmode': 'tel'
            }),
            'mobile_number': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'মোবাইল নম্বর',
                'inputmode': 'tel'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'বর্তমান ঠিকানা'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'জরুরি যোগাযোগের নাম'
            }),
            'emergency_phone': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'জরুরি ফোন নম্বর',
                'inputmode': 'tel'
            }),
            'department': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'designation': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'পদবি'
            }),
            'profile_image': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-sm',
                'accept': 'image/*'
            }),
        }

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['staff', 'leave_type', 'start_date', 'end_date']
        widgets = {
            'staff': forms.Select(attrs={'class': 'form-select'}),
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class PublicHolidayForm(forms.ModelForm):
    class Meta:
        model = PublicHoliday
        fields = ['name', 'date', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ছুটির নাম লিখুন'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'ছোট বিবরণ (ঐচ্ছিক)'}),
        }