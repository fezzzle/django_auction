from django.urls import path, include

from . import views

app_name = 'auction'
urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create, name='create'),
    path('auctions/', views.auctions, name='auctions'),
    # path('accounts/', include('django.contrib.auth.urls')),
    path('auctions/<int:auction_id>', views.detail, name='detail'),
    path('auctions/delete_auctions', views.delete_auctions, name='delete_auctions'),
    path('auctions/my_auctions', views.my_auctions, name='my_auctions'),
    path('auctions/bid/<int:auction_id>', views.bid, name='bid'),
    path('auctions/searchbar/', views.searchbar, name='searchbar'),
]
