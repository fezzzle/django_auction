import json
from time import time

from django.shortcuts import render
from .models import Auction, Bid, CustomUser, AuctionImage
from datetime import datetime, timezone
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, Http404
from django.db.models import Q
from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import password_validation

from itertools import chain

import logging

logger = logging.getLogger("mylogger")


def index(request):
    auctions_list = Auction.objects.all()
    for a in auctions_list:
        a.resolve()
    current_user = request.user
    return render(request, 'auction/index.html', {"auctions_list": auctions_list, "user": current_user})


def detail(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id)
    bid = Bid.objects.filter(auction=auction)
    images = AuctionImage.objects.filter(auction=auction)
    print(f"IMAGES IN DETAIL: {images}")
    auction.resolve()
    auction.save()
    json_ctx = json.dumps({"auction_end_stamp": int(auction.expire.timestamp() * 1000)})
    cancel_auction_button = request.POST.get('cancel_auction')
    if bid:
        bid = bid.first().amount
    if request.user == auction.author or not request.user.is_authenticated:
        own_auction = True
        if cancel_auction_button:
            try:
                auction.is_active = False
                auction.save()
                return render(request, "auction/detail.html", {"auction": auction, "own_auction": own_auction, "images": images})
            except Exception as e:
                logger.info(e)
        return render(request, "auction/detail.html", {"auction": auction, "own_auction": own_auction, "bid": bid, "json_ctx": json_ctx, "images": images})
    return render(request, "auction/detail.html", {"auction": auction, 'bid': bid, "json_ctx": json_ctx, "images": images})


@login_required
def create(request):
    if request.method == 'POST':
        try:
            title = request.POST['title']
            description = request.POST['description']
            min_value = request.POST['min_value']
            duration = request.POST['duration']
            buy_now = int(request.POST['buy_now'])
            images = request.FILES.getlist("file[]")
            logger.info(f"IMAGES ARE: {images}")
            if not title or not description or not min_value:
                raise KeyError
            if int(min_value) < 0 or int(duration) < 10:
                raise ValueError
            else:
                if buy_now == 0:
                    buy_now = None
                elif int(min_value) > int(buy_now):
                    raise ValueError
        except KeyError as err:
            messages.warning(request, 'Please fill all the fields!')
            return render(request, "auction/create.html")
        except ValueError:
            messages.warning(request, 'Buy now needs to be bigger than minimum bid or input was wrong!')
            return render(request, "auction/create.html")
        else:
            auction = Auction()
            auction.author = request.user
            auction.title = title
            auction.description = description
            auction.min_value = int(min_value)
            auction.date_added = timezone.now()
            auction.total_auction_duration = duration
            auction.buy_now = buy_now
            auction.save()
            for img in images:
                auction_img = AuctionImage(auction=auction, image=img)
                print(f"ONE IMG IS: {img}")
                auction_img.image = img
                auction_img.save()
            messages.success(request, 'Your listing has been created!')
            return HttpResponseRedirect(reverse('auction:detail', args=(auction.id,)))
    else:
        return render(request, "auction/create.html")


def auctions(request):
    auction_list = Auction.objects.all().order_by('-date_added')
    for a in auction_list:
        a.resolve()
    return render(request, "auction/auctions.html", {"auction_list": auction_list})


@login_required
def delete_auctions(request):
    if request.user.is_superuser:
        auctions = Auction.objects.all().delete()
        logger.info(f"All auctions deleted")
    else:
        logger.info("You need to be a superuser")

    return render(request, "auction/deleted.html")
    # return HttpResponseRedirect(reverse('auction:detail', args=(auction.id,)))


@login_required
def my_auctions(request):
    my_auctions = Auction.objects.filter(author=request.user).order_by("-date_added")
    for a in my_auctions:
        a.resolve()
    return render(request, "auction/my_auctions.html", {'my_auctions': my_auctions})


@login_required
def my_bids(request):
    my_bids = Bid.objects.all().filter(bidder_id=request.user.id).order_by('-time_added')
    return render(request, "auction/my_bids.html", {'my_bids': my_bids})


@login_required
def bid(request, auction_id):
    buy_now_button = request.POST.get('buy_now')
    bid_amount = int(request.POST['amount'])
    auction = get_object_or_404(Auction, pk=auction_id)
    auction.resolve()
    bid = Bid.objects.filter(bidder=request.user).filter(auction=auction).first()
    if not auction.is_active:
        messages.warning(request, 'Auction is not active!')
        return render(request, "auction/detail.html", {'auction': auction})
    if not bid:
        bid = Bid()
        bid.auction = auction
        bid.bidder = request.user
        bid.time_added = datetime.now(timezone.utc)
    try:
        # When user clicks buy now
        # if request.method == 'POST' and 'buy_now_button' in request.POST:
        if buy_now_button:
            auction.total_auction_duration = 0
            bid.bidder = request.user
            bid.amount = auction.buy_now
            bid.save()
            auction.resolve()
            auction.save()
        # When user bids instead of buynow
        elif bid_amount:
            print(f"TYPE OF bid_amount: {type(bid_amount)}")
            print(f"TYPE OF bid.amount IN 166: {type(bid.amount)}")
            print(f"bid_____amount: {bid_amount}")
            print(f"bid.....amount: {bid.amount}")
            if bid_amount < auction.min_value or bid_amount > auction.buy_now:
                raise ValueError
            if bid_amount <= bid.amount:
                messages.warning(request, 'Inside first')
                # messages.warning(request, 'You need to enter a bigger bid than the previous amount!')
                return render(request, "auction/detail.html", {'auction': auction, 'user_bid': bid.highest_user_bid})

            bid.amount = bid_amount
            bid.save()
            
            if bid.amount <= auction.active_bid_value:
                messages.warning(request, 'Inside second')
                # messages.warning(request, 'You need to enter a bigger bid than the previous amount!')
                return render(request, "auction/detail.html", {'auction': auction, 'user_bid': bid.highest_user_bid})
            if bid.amount == auction.buy_now:
                auction.active_bid_value = bid.amount
                bid.save()
                auction.resolve()
                auction.save()

            auction.active_bid_value = bid.amount
    except ValueError:
        messages.warning(request, 'You have entered invalid input or less than min value')
        return render(request, "auction/detail.html", {'auction': auction, 'user_bid': bid.highest_user_bid})
    else:
        auction.resolve()
        bid.save()
        auction.save()
        messages.success(request, f"You successfully bidded {bid.amount} eur!")
        return render(request, "auction/detail.html", {'auction': auction, 'bid': bid.highest_user_bid})


def searchbar(request):
    search = request.GET.get('search')
    auction_list = Auction.objects.all()
    if search:
        auction_list = auction_list.filter(
            Q(title__startswith=search) |
            Q(title__contains=search)
        )
        return render(request, 'auction/search_result.html', {'auction_list': auction_list})
    else:
        return render(request, 'auction/search_result.html', {'auction_list': auction_list})


@login_required
def profile(request):
    user = get_object_or_404(CustomUser, pk=request.user.id)
    if request.method == 'POST' and 'email_change' in request.POST:
        logger.info(f'REQUEST.POST {request.POST}')
        logger.info(f'REQUEST.POST {type(request.POST)}')
        try:
            email = request.POST['email']
            validate_email(email)
        except ValidationError as e:
            messages.warning(request, 'Please enter a valid email!')
        else:
            messages.success(request, "Email successfully changed!")
            user.email = email
            user.save()
    if request.method == 'POST' and 'password_change' in request.POST:
        try:
            password1 = request.POST['user_password1']
            password2 = request.POST['user_password2']
            if password1 and password2 and password1 != password2:
                raise ValidationError('Password did not match')
            password_validation.validate_password(password1)
        except ValidationError as e:
            messages.warning(request, f"{e.args[0]}")
        else:
            user = CustomUser.objects.get(pk=request.user.id)
            if user.check_password(password1):
                messages.warning(request, 'You already have used this password')
                return render(request, "auction/profile.html", {"user": user})
            user.set_password(password1)
            user.save()
            messages.success(request, "Successfully changed password!")
    if request.method == 'POST' and 'location_change' in request.POST:
        try:
            location = request.POST['location']
        except Exception as e:
            messages.warning(request, 'Something went wrong when changing location')
        else:
            messages.success(request, "Location successfully changed!")
            user.location = location
            user.save()

    return render(request, "auction/profile.html", {"user": user})
