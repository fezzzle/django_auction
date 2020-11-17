import json
from time import time

from django.shortcuts import render
from .models import Auction, Bid, CustomUser
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
from django.core.files.storage import FileSystemStorage


import logging

logger = logging.getLogger("mylogger")


def index(request):
    auctions_list = Auction.objects.all()
    for a in auctions_list:
        a.resolve()
    current_user = request.user
    return render(request, 'auction/index.html', {'auctions_list': auctions_list, 'user': current_user})


def detail(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id)
    bid = Bid.objects.filter(auction=auction)
    auction.resolve()
    auction.visits += 1
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
                return render(request, "auction/detail.html", {"auction": auction, "own_auction": own_auction})
            except Exception as e:
                logger.info(e)
        return render(request, "auction/detail.html", {"auction": auction, "own_auction": own_auction, "bid": bid, "json_ctx": json_ctx})
    return render(request, "auction/detail.html", {"auction": auction, 'bid': bid, "json_ctx": json_ctx})


@login_required
def create(request):
    if request.method == 'POST':
        try:
            title = request.POST['title']
            description = request.POST['description']
            min_value = request.POST['min_value']
            duration = request.POST['duration']
            buy_now = int(request.POST['buy_now'])
            pic = request.FILES['myfile']
            if not title or not description or not min_value:
                raise KeyError
            if buy_now == 0:
                buy_now = None
            else:
                if int(min_value) > int(buy_now):
                    raise ValueError
        except KeyError as err:
            messages.warning(request, 'Please fill all the fields!')
            return render(request, "auction/create.html")
        except ValueError:
            messages.warning(request, 'Buy now needs to be bigger than minimum bid!')
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
            auction.image = pic
            auction.save()
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
        if buy_now_button:
            auction.total_auction_duration = 0
            auction.save()
            bid.bidder = request.user
            bid.amount = auction.buy_now
            bid.save()
            auction.resolve()
        # When user bids instead of buynow
        elif bid_amount:
            if int(bid_amount) < auction.min_value:
                raise ValueError
            if bid_amount <= bid.amount:
                messages.warning(request, 'You need to enter a bigger bid than the previous amount!')
                return render(request, "auction/detail.html", {'auction': auction, 'user_bid': bid.highest_user_bid})
            bid.amount = int(bid_amount)
            if bid.amount <= auction.active_bid_value:
                messages.warning(request, 'You need to enter a bigger bid than the previous amount!')
                return render(request, "auction/detail.html", {'auction': auction, 'user_bid': bid.highest_user_bid})
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
    email_change = request.POST.get('email_change')
    password_change = request.POST.get('password_change')
    location_change = request.POST.get('location_change')
    user = get_object_or_404(CustomUser, pk=request.user.id)
    logger.info(f"USER TYPE IS {type(user)}")
    logger.info(f"USER IS {user}")

    if email_change:
        try:
            email = request.POST['email']
            validate_email(email)
        except ValidationError as e:
            messages.warning(request, 'Please enter a valid email!')
        else:
            messages.success(request, "Email successfully changed!")
            user.email = email
            user.save()
    if password_change:
        try:
            password1 = request.POST['user_password1']
            password2 = request.POST['user_password2']
            if password1 != password2:
                raise ValidationError('Password did not match')
        except ValidationError as e:
            messages.warning(request, "Your passwords did not match. Try again!")
        else:
            user = CustomUser.objects.get(pk=request.user.id)
            if user.check_password(password1):
                messages.warning(request, 'You already have used this password')
                return render(request, "auction/profile.html", {"user": user})
            user.set_password(password1)
            user.save()
            messages.success(request, "Successfully changed password!")

    if location_change:
        try:
            location = request.POST['location']
        except Exception as e:
            messages.warning(request, 'Something went wrong when changing location')
        else:
            messages.success(request, "Location successfully changed!")
            user.location = location
            user.save()

    return render(request, "auction/profile.html", {"user": user})
