from django.contrib import admin
from .models import Wishlist, WishlistItem

class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items_display', 'created_at', 'updated_at')
    search_fields = ('user__email',)
    inlines = [WishlistItemInline]

    @admin.display(description='Total Items')
    def total_items_display(self, obj):
        return obj.total_items


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('wishlist', 'product', 'created_at')
    search_fields = ('product__title', 'wishlist__user__email')
