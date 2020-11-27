from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

from django.urls import reverse
from django_resized import ResizedImageField

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .utils import path_and_rename

import logging

logger = logging.getLogger("mylogger")


class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    location = models.CharField(max_length=30, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    first_name = models.CharField(max_length=15, blank=True, null=True)
    last_name = models.CharField(max_length=15, blank=True, null=True)

    def get_absolute_url(self):
        """Returns the url to access a particular instance of the model."""
        return reverse('auction:profile', args=[str(self.username)])

    def __str__(self):
        return self.username


class Category(models.Model):
    description = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=25, primary_key=True)
    logo = ResizedImageField(upload_to='media/logos', blank=True)

    def __str__(self):
        return self.name


class Auction(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    item_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(max_length=500)
    min_value = models.IntegerField()
    buy_now = models.IntegerField(blank=True, null=True)
    date_added = models.DateTimeField(datetime.now, blank=True, help_text='date added')
    date_ended = models.DateTimeField(blank=True, null=True, help_text='date added')
    active_bid_value = models.IntegerField(blank=True, null=True, default=0)
    is_active = models.BooleanField(default=True)
    total_auction_duration = models.IntegerField()
    final_value = models.IntegerField(blank=True, null=True)
    winner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True, 
                               related_name="auction_winner",
                               related_query_name="auction_winner")

    class Meta:
        ordering = ['date_added']

    def get_absolute_url(self):
        return reverse('auction:detail', args=[str(self.id)])

    def get_first_image(self):
        return self.auctionimage_set.first()

    def resolve(self):
        if self.is_active:
            highest_bid = Bid.objects.filter(auction=self).order_by('-amount').first()
            if self.has_expired():
                if highest_bid:
                    self.winner = highest_bid.bidder
                    self.final_value = highest_bid.amount
                    self.date_ended = datetime.now()
                self.is_active = False
                self.save()
            if self.active_bid_value and self.buy_now != 0:
                if self.active_bid_value >= self.buy_now:
                    self.active_bid_value = highest_bid.amount
                    self.winner = highest_bid.bidder
                    self.final_value = highest_bid.amount
                    self.is_active = False
                    self.date_ended = datetime.now()
                    self.save()

    def has_expired(self):
        now = timezone.now()
        auction_end = self.date_added + timedelta(minutes=self.total_auction_duration)
        if now > auction_end:
            return True
        return False

    @property
    def seconds_remaining(self):
        if self.is_active:
            now = datetime.now(timezone.utc)
            expire = self.date_added + timedelta(minutes=self.total_auction_duration)
            time_remaining = (expire - now).total_seconds()
            return time_remaining
        else:
            return 0

    @property
    def expire(self):
        return self.date_added + timedelta(minutes=self.total_auction_duration)

    @property
    def highest_auction_bid(self):
        return self.active_bid_value

    def __str__(self):
        return self.title


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    bidder = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="bidder")
    time_added = models.DateTimeField()
    amount = models.IntegerField(default=0)

    @property
    def highest_user_bid(self):
        return self.amount

    def __str__(self):
        return str(self.amount)


class AuctionImage(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=path_and_rename)

