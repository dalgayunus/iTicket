from django.contrib import admin
from .models import User, Profile
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('phone_number', 'role', 'email_verified', 'phone_verified')}),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar', 'date_of_birth', 'country', 'city', 'address_line1', 'address_line2', 'postal_code', 'company_name', 'bio')
    search_fields = ('user__username', 'user__email', 'store_name')
    list_filter = ('country', 'city')