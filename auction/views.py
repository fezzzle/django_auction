import json
from time import time

from django.shortcuts import render
from .models import Auction, Bid
from datetime import datetime, timezone
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib import messages

from django.contrib.auth.decorators import login_required


import logging

logger = logging.getLogger("mylogger")

def index(request):
    auctions_list = Auction.objects.all()
    for a in auctions_list:
        a.resolve()
    current_user = request.user
    pic_url = "https://picsum.photos/200"
    return render(request, 'auction/index.html', {'auctions_list': auctions_list, 'user': current_user, 'pic': pic_url})

def detail(request, auction_id):
    auction = get_object_or_404(Auction, pk=auction_id)
    bid = Bid.objects.filter(auction=auction)
    auction.resolve()
    auction.visits += 1
    auction.save()
    json_ctx = json.dumps({"auction_end_stamp": int(auction.expire.timestamp() * 1000)})
    if bid:
        bid = bid.first().amount
    if request.user == auction.author or not request.user.is_authenticated:
        own_auction = True
        return render(request, "auction/detail.html", {"auction": auction, "own_auction": own_auction, "bid": bid, "json_ctx": json_ctx})
    return render(request, "auction/detail.html", {"auction": auction, 'bid': bid, "json_ctx": json_ctx})


@login_required
def create(request):
    # submit_button = request.POST.get('submit_button')
    submit_button = request.POST.get('submit_button')
    # logger.info(f"Submit buttons type: {type(submit_button)}")
    # logger.info(f"User sending the request: {request.user}")
    if submit_button:
        try:
            title = request.POST['title']
            description = request.POST['description']
            min_value = request.POST['min_value']
            duration = request.POST['duration']
            logger.info(f"values: {title, description, min_value}")
            
            if not title or not description or not min_value:
                raise KeyError
        except KeyError:
            messages.warning(request, 'Please fill all the fields!')
            return render(request, "auction/create.html")
        else:
            auction = Auction()
            auction.author = request.user
            auction.title = title
            auction.description = description
            auction.min_value = min_value
            auction.date_added = timezone.now()
            auction.total_auction_duration = duration
            auction.save()
            messages.success(request, 'Your listing has been created!')
            return HttpResponseRedirect(reverse('auction:detail', args=(auction.id,)))
    else:
        return render(request, "auction/create.html")


def auctions(request):
    auction_list = Auction.objects.all().order_by('-date_added')
    pic_url = "https://picsum.photos/200"
    for a in auction_list:
        a.resolve()
    return render(request, "auction/auctions.html", {"auction_list": auction_list, "pic": pic_url})

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
    auction = get_object_or_404(Auction, pk=auction_id)
    auction.resolve()

    bid = Bid.objects.filter(bidder=request.user).filter(auction=auction).first()

    if not auction.is_active:
        messages.warning(request, 'Auction is not active!')
        return render(request, "auction/detail.html", {'auction': auction})
    
    try:
        bid_amount = int(request.POST['amount'])

        if not bid_amount or int(bid_amount) < auction.min_value:
            raise ValueError

        if not bid:
            bid = Bid()
            bid.auction = auction
            bid.bidder = request.user

        if bid:
            if bid_amount <= bid.amount:
                messages.warning(request, 'You need to enter a bigger bid than the previous amount!')        
                return render(request, "auction/detail.html", {'auction': auction, 'bid': bid.highest_bid})

        bid.amount = int(bid_amount)
        bid.time_added = datetime.now(timezone.utc)
    except ValueError:
        messages.warning(request, 'You have entered invalid input or less than min value')
        return render(request, "auction/detail.html", {'auction': auction, 'bid': bid.highest_bid})

    else:
        bid.save()
        messages.success(request, f"You successfully bidded {bid.amount} eur!")
        return render(request, "auction/detail.html", {'auction': auction, 'bid': bid.highest_bid})
        # return HttpResponseRedirect(reverse('auction:auctions', args=()))

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
        return render(request, 'auction/search_result.html', {'auction_list':auction_list})

