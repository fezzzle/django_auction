from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from auction.models import Auction, Bid, CustomUser, AuctionImage


class CustomUserAdmin(BaseUserAdmin):
    fieldsets = (
        *BaseUserAdmin.fieldsets,  # original form fieldsets, expanded
        (                      # new fieldset added on to the bottom
            'Custom Field Heading',  # group heading of your choice; set to None for a blank space instead of a header
            {
                'fields': (
                    'is_bot_flag',
                ),
            },
        ),
    )

admin.site.register(CustomUser, BaseUserAdmin)
admin.site.register(Auction)
admin.site.register(Bid)
admin.site.register(AuctionImage)
