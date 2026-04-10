from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from store.models import UserProfile
from store.security import sanitize_text, validate_no_script


class RegisterForm(UserCreationForm):
    email      = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name  = forms.CharField(max_length=50, required=True)

    class Meta:
        model  = User
        fields = [
            'username', 'first_name', 'last_name',
            'email', 'password1', 'password2'
        ]

    def clean_first_name(self):
        value = self.cleaned_data.get('first_name', '')
        validate_no_script(value)
        return sanitize_text(value)

    def clean_last_name(self):
        value = self.cleaned_data.get('last_name', '')
        validate_no_script(value)
        return sanitize_text(value)

    def clean_email(self):
        email = self.cleaned_data.get('email', '')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email.lower().strip()

    def clean_username(self):
        username = self.cleaned_data.get('username', '')
        validate_no_script(username)
        return username


class UpdateUserForm(forms.ModelForm):
    email      = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name  = forms.CharField(max_length=50, required=True)

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def clean_first_name(self):
        value = self.cleaned_data.get('first_name', '')
        validate_no_script(value)
        return sanitize_text(value)

    def clean_last_name(self):
        value = self.cleaned_data.get('last_name', '')
        validate_no_script(value)
        return sanitize_text(value)


class UpdateProfileForm(forms.ModelForm):
    class Meta:
        model   = UserProfile
        fields  = ['avatar', 'bio', 'phone', 'address']
        widgets = {
            'bio':     forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_bio(self):
        value = self.cleaned_data.get('bio', '')
        validate_no_script(value)
        return sanitize_text(value)

    def clean_address(self):
        value = self.cleaned_data.get('address', '')
        validate_no_script(value)
        return sanitize_text(value)

    def clean_phone(self):
        value = self.cleaned_data.get('phone', '')
        import re
        if value and not re.match(r'^[\d\s\+\-\(\)]+$', value):
            raise forms.ValidationError('Enter a valid phone number.')
        return value.strip()