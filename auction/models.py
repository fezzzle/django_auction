from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .utils import path_and_rename

import logging

logger = logging.getLogger("mylogger")


class CustomUser(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    location = models.CharField(max_length=100)


class Auction(models.Model):
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    min_value = models.IntegerField()
    buy_now = models.IntegerField(blank=True, null=True)
    date_added = models.DateTimeField(datetime.now, blank=True)
    active_bid_value = models.IntegerField(blank=True, null=True, default=0)
    is_active = models.BooleanField(default=True)
    total_auction_duration = models.IntegerField()
    winner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True, 
                              related_name="auction_winner",
                              related_query_name="auction_winner")
    final_value = models.IntegerField(blank=True, null=True)

    def get_first_image(self):
        return self.auctionimage_set.first()

    def resolve(self):
        if self.is_active:
            highest_bid = Bid.objects.filter(auction=self).order_by('-amount').first()
            if self.has_expired():
                if highest_bid:
                    self.winner = highest_bid.bidder
                    self.final_value = highest_bid.amount
                self.is_active = False
                self.save()
            if self.active_bid_value and self.buy_now is not 0:
                if self.active_bid_value >= self.buy_now:
                    self.active_bid_value = highest_bid.amount
                    self.winner = highest_bid.bidder
                    self.final_value = highest_bid.amount
                    self.is_active = False
                    self.save()

    def has_expired(self):
        now = timezone.now()
        logger.info(f"TIME IS NOW: {now}")
        auction_end = self.date_added + timedelta(minutes=self.total_auction_duration)
        logger.info(f"AUCTION END IS: {auction_end}")
        if now > auction_end:
            return True
        else:
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
        if self.active_bid_value:
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
        if self.amount:
            return self.amount

    def __str__(self):
        return str(self.amount)


class AuctionImage(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=path_and_rename, max_length=255, null=True, blank=True)

