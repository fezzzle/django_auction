from django.contrib.auth import views as auth_views
from django.views import generic
from django.urls import reverse_lazy

# from .forms import LoginForm, RegisterForm
from .forms import UserLoginForm, RegistrationForm


class LogoutView(auth_views.LogoutView):
    template_name: "register/logged_out.html"


class LoginView(auth_views.LoginView):
    form_class = UserLoginForm
    template_name = 'register/login.html'


class RegisterView(generic.CreateView):
    form_class = RegistrationForm
    template_name = 'register/register.html'
    success_url = reverse_lazy('login')
