from django.contrib.auth import views as auth_views
from django.views import generic
from django.urls import reverse_lazy

from auction.forms import LoginForm, RegisterForm


class LogoutView(auth_views.LogoutView):
    template_name: "registration/logged_out.html"


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'


class RegisterView(generic.CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
