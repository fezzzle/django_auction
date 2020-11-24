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

import logging

logger = logging.getLogger("mylogger")


def index(request):
    all_auctions = Auction.objects.all()
    last_added = Auction.objects.all().order_by('-date_added')[:5]
    ending_soon = Auction.objects.all().order_by('total_auction_duration')[:5]
    for a in all_auctions:
        a.resolve()
    current_user = request.user
    return render(
        request,
        'auction/index.html',
        {
            "all_auctions": all_auctions,
            "user": current_user,
            "last_added": last_added,
            "ending_soon": ending_soon
        })


def detail(request, auction_id):

    # Buy using get method, we pass in default value and then set every time user visits detail view, request.session['num_visits'] = num_visits + 1
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    auction = get_object_or_404(Auction, pk=auction_id)
    bid = Bid.objects.filter(auction=auction)
    images = AuctionImage.objects.filter(auction=auction)
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
                return render(
                    request,
                    "auction/detail.html",
                    {
                        "auction": auction,
                        "own_auction": own_auction,
                        "images": images
                    })
            except Exception as e:
                logger.info(e)
        return render(
            request, 
            "auction/detail.html", 
            {
                "auction": auction,
                "own_auction": own_auction,
                "bid": bid,
                "json_ctx": json_ctx,
                "images": images
            })
    return render(
        request, 
        "auction/detail.html",
        {
            "auction": auction,
            'bid': bid,
            "json_ctx": json_ctx,
            "images": images
        })


@login_required
def create(request):
    if request.method == 'POST':
        try:
            _, title, description, duration, min_value, buy_now, _ = list(request.POST.dict().values())
            images = request.FILES.getlist("file_upload")
            if not title or not description or not min_value or not images:
                raise KeyError
            if int(min_value) < 0 or int(duration) < 10:
                raise ValueError
            else:
                if buy_now == "":
                    buy_now = 0
                elif int(min_value) > int(buy_now):
                    raise ValueError
        except KeyError as e:
            messages.warning(request, e)
            messages.warning(request, 'Please fill all the fields!')
            return render(request, "auction/create.html")
        except ValueError as e:
            messages.warning(request, e)
            messages.warning(request, 'Buy now needs to be bigger than minimum bid or input was wrong!')
            return render(request, "auction/create.html")
        else:
            auction = Auction()
            auction.author = request.user
            auction.title = title
            auction.description = description
            auction.min_value = int(min_value)
            auction.date_added = timezone.now()
            auction.total_auction_duration = int(duration)
            auction.buy_now = int(buy_now)
            auction.save()
            for img in images:
                auction_img = AuctionImage(auction=auction, image=img)
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
    bid_amount = int(request.POST['amount'])
    auction = get_object_or_404(Auction, pk=auction_id)
    images = AuctionImage.objects.filter(auction=auction)
    json_ctx = json.dumps({"auction_end_stamp": int(auction.expire.timestamp() * 1000)})
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
        if request.method == 'POST' and 'buy_now' in request.POST:
            auction.total_auction_duration = 0
            bid.bidder = request.user
            bid.amount = auction.buy_now
            auction.active_bid_value = bid.amount
            bid.save()
            auction.resolve()
        #When user bids instead of buynow
        elif request.method == 'POST' and 'amount' in request.POST:
            if bid_amount <= bid.amount or auction.buy_now < bid_amount:
                messages.warning(request, 'Entered bid is not correct!')
                return render(
                    request, 
                    "auction/detail.html",
                    {
                        "auction": auction,
                        "bid": bid.highest_user_bid,
                        "images": images,
                        "json_ctx": json_ctx
                    })
            bid.amount = bid_amount
            bid.save()
            if bid.amount <= auction.active_bid_value:
                messages.warning(request, 'You need to enter a bigger bid than the previous amount!')
                return render(
                    request,
                    "auction/detail.html",
                    {
                        "auction": auction,
                        "bid": bid.highest_user_bid,
                        "images": images,
                        "json_ctx": json_ctx
                    })
            if auction.buy_now:
                if bid_amount < auction.min_value or bid_amount > auction.buy_now:
                    raise ValueError
            auction.active_bid_value = bid.amount
    except ValueError as e:
        messages.warning(request, e)
        messages.warning(request, 'You have entered invalid input or less than min value')
        return render(
            request,
            "auction/detail.html",
            {
                "auction": auction,
                "user_bid": bid.highest_user_bid,
                "images": images, "json_ctx": json_ctx})
    else:
        if not auction.is_active:
            auction.active_bid_value = bid.amount
        auction.resolve()
        bid.save()
        auction.save()
        messages.success(request, f"You successfully bidded {bid.amount} eur!")
        return render(request, "auction/detail.html", {'auction': auction, 'bid': bid.highest_user_bid, "images": images, "json_ctx": json_ctx})


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
def profile(request, **username):
    if len(username) > 0:
        if username['username'] == str(request.user):
            return render(
                request,
                "auction/profile.html",
                {
                    "user": request.user
                })
        else:
            user = CustomUser.objects.get(username=username['username'])
            user_auctions = Auction.objects.filter(
                author=user.id
                ).order_by("-date_added")
            user = get_object_or_404(CustomUser, username=username['username'])
            return render(
                request,
                "auction/user.html",
                {
                    "user": user,
                    "user_auctions": user_auctions
                })
    user = get_object_or_404(CustomUser, pk=request.user.id)
    if request.method == 'POST' and request.POST.get('email'):
        try:
            email = request.POST.get('email')
            validate_email(email)
        except ValidationError as e:
            messages.warning(request, 'Please enter a valid email!')
        else:
            user.email = email
            user.save()
            messages.success(request, "Email successfully changed!")
    if request.method == 'POST' and request.POST.get('first-name'):
        try:
            first_name = request.POST.get('first-name')
        except Exception as e:
            messages.warning(request, e)
        else:
            user.first_name = first_name
            user.save()
            messages.success(request, "First name set!")

    if request.method == 'POST' and request.POST.get('last-name'):
        try:
            last_name = request.POST.get('last-name')
        except Exception as e:
            messages.warning(request, e)
        else:
            user.last_name = last_name
            user.save()
            messages.success(request, "Last name set!")

    if request.method == 'POST' and request.POST.get('phone'):
        try:
            phone = request.POST.get('phone')
        except Exception as e:
            messages.warning(request, e)
        else:
            user.phone = phone
            user.save()
            messages.success(request, "Phone number set!")

    if request.method == 'POST' and request.POST.get('password_change'):
        try:
            password1 = request.POST.get('user_password1')
            password2 = request.POST.get('user_password2')
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

    if request.method == 'POST' and request.POST.get('location'):
        try:
            location = request.POST.get('location')
        except Exception as e:
            messages.warning(
                request,
                'Something went wrong when changing location'
            )
        else:
            user.location = location
            user.save()
            messages.success(request, "Location successfully changed!")
    return render(request, "auction/profile.html", {"user": user})


def handler404(request, err):
    return render(request, 'auction/404.html', status=404)


def handler500(request):
    return render(request, 'auction/500.html', status=500)