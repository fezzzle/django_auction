from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

import logging

logger = logging.getLogger("mylogger")


class Auction(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    min_value = models.IntegerField()
    date_added = models.DateTimeField(datetime.now, blank=True)
    is_active = models.BooleanField(default=True)
    total_auction_duration = models.IntegerField()
    winner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, 
                              related_name="auction_winner",
                              related_query_name="auction_winner")
    final_value = models.IntegerField(blank=True, null=True)

    def resolve(self):
        if self.is_active:
            if self.has_expired():
                highest_bid = Bid.objects.filter(auction=self).order_by('-amount').first()
                logger.info(f"HIGHTEST BID: {highest_bid}")
                if highest_bid:
                    self.winner = highest_bid.bidder
                    self.final_value = highest_bid.amount
                self.is_active = False
                self.save()

    def has_expired(self):
        now = timezone.now()
        # logger.info(f"NOW IS: {now}")
        auction_end = self.date_added + timedelta(minutes=self.total_auction_duration)
        # logger.info(f"AUCTION END IS: {auction_end}")
        # logger.info(f"TIME NOW IS BIGGER THAN AUCTION END: {now > auction_end}")
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

    def __str__(self):
        return self.title



class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bidder")
    time_added = models.DateTimeField()
    amount = models.IntegerField(default=1)

    @property
    def highest_bid(self):
        if self.amount:
            return self.amount

