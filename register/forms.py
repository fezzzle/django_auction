from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms
from django.utils.translation import ugettext_lazy as _


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(max_length=30)
    username = forms.CharField(max_length=15)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    location = forms.CharField(max_length=30, required=False)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = get_user_model()
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'location',
            'phone',
            'password1',
            'password2'
            )


class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)

    username = forms.EmailField(widget=forms.TextInput(
        attrs={
            'autofocus': 'autofocus',
            # 'class': 'form-control', 
            # 'placeholder': 'Username/email', 
            'id': 'username'
            }))
    password = forms.CharField(widget=forms.PasswordInput(
        attrs={
            # 'class': 'form-control',
            # 'placeholder': 'Enter password',
            'id': 'password',
        }
))
