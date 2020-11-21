from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django import forms


class RegisterForm(UserCreationForm):
    username = forms.CharField(max_length=15)
    email = forms.EmailField(max_length=30)
    location = forms.CharField(max_length=30)
    phone = forms.CharField(max_length=15)

    class Meta:
        model = get_user_model()
        fields = ('email', 'username', 'location', 'phone', 'password1', 'password2')


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'autofocus': 'autofocus', 'placeholder': 'Email / Username'}))
