# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth import logout, authenticate, login
# from django.http import HttpResponse
# from django.shortcuts import render, redirect

# def register(request):
#     if request.user.is_authenticated:
#         return redirect('auction:index')
#     if request.method == "POST":
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             username = form.cleaned_data.get('username')
#             login(request, user)
#             return redirect("/")
#             # return HttpResponseRedirect(reverse('auctions'))
#         else:
#             for msg in form.error_messages:
#                 # print(form.error_messages[msg])
#                 error_message = form.error_messages[msg]

#             return render(request = request,
#                           template_name = "registration/register.html",
#                           context={
#                               "form": form,
#                               "error_message": error_message,
#                           })

#     form = UserCreationForm
#     return render(request = request,
#                   template_name = "registration/register.html",
#                   context={"form":form})


from django.contrib.auth import views as auth_views
from django.views import generic
from django.urls import reverse_lazy

from auction.forms import LoginForm, RegisterForm


class LogoutView(auth_views.LogoutView):
    template_name: "registration/logout.html"


class LoginView(auth_views.LoginView):
    form_class = LoginForm
    template_name = 'registration/login.html'


class RegisterView(generic.CreateView):
    form_class = RegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('login')
