from django.urls import path
from . import views

app_name = 'auction'

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create, name='create'),
    path('auctions/', views.auctions, name='auctions'),
    path('auctions/<int:auction_id>', views.detail, name='detail'),
    path('auctions/delete_auctions', views.delete_auctions, name='delete_auctions'),
    path('auctions/my_auctions', views.my_auctions, name='my_auctions'),
    path('auctions/<int:auction_id>/bid/', views.bid, name='bid'),
    path('searchbar/', views.searchbar, name='searchbar'),
    path('auctions/my_bids', views.my_bids, name='my_bids'),
    path('profile/<username>', views.profile, name='profile'),
    path('profile/', views.profile, name='profile'),
    ]