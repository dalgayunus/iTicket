from django.contrib import admin
from .models import Event
from .models import Ticket
from .models import Category
from .models import PromoCode
from .models import Order
from .models import Review
from .models import Wallet


def mark_as_depleted(modeladmin, request, queryset):
    queryset.update(quantity_avaible=0)

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date', 'venue', 'language']
    list_filter = ['venue', 'date']
    search_fields = ['title']
    ordering = ['-date']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['event', 'name', 'price', 'current_price', 'discount_percentage', 'quantity_avaible']
    list_filter = ['event', 'price']
    list_display_links = ['event']
    search_fields = ['event', 'name']
    ordering = ['price']
    actions = [mark_as_depleted]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']

@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percentage', 'valid_from', 'valid_until', 'usage_limit', 'used_count', 'is_active', 'created_by')
    search_fields = ('code',)
    list_filter = ('is_active',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'status', 'ordered_at', 'final_price')
    list_filter = ('status',)
    search_fields = ('customer__username',)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')