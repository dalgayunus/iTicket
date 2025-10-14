from django.db import models
from django.utils import timezone
from datetime import timedelta
from user.models import User
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return self.name


class Event(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    date = models.DateTimeField()
    venue = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    category = models.ManyToManyField(Category, related_name='events', blank=True)
    language = models.CharField(max_length=255, choices=[
        ('EN', 'English'),
        ('AZ', 'Azerbaijani'),
        ('TR', 'Turkish'),
        ('RU', 'Russian'),
    ], default='EN')
    is_active = models.BooleanField(default=True)
    class Meta:
        ...
    
    def __str__(self):
        return self.title
    
    def is_recent(self):
        now = timezone.now()
        return now < self.date < now + timedelta(days=31)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Ticket(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity_avaible = models.PositiveIntegerField()
    def __str__(self):
        return f"{self.event}, {self.name}"

    def quantity(self):
        return self.quantity_avaible > 0
    

class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ManyToManyField(Ticket, related_name='orders', through='OrderItem', blank=True)    
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        CANCELLED = 'cancelled', 'Cancelled'
        RETURNED = 'returned', 'Returned'

    status = models.CharField(max_length=255, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    ordered_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_price(self):
        return sum(item.price * item.quantity for item in self.orderitems.all())
    
    
    promo_code = models.ForeignKey('PromoCode', on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    final_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


    def apply_promo_instance(self, promo=None):
        total = self.total_price()
        discount = (total * promo.discount_percentage) / Decimal('100.00')
        self.discount_amount = discount.quantize(Decimal('0.01'))
        self.promo_code = promo
        self.final_price = (total - self.discount_amount).quantize(Decimal('0.01'))

        self.save()
        return self.final_price
    

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='orderitems')
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='orderitems')
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)


class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('user.User', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_promocodes')

    class Meta:
        ordering = ['-valid_from']

    def __str__(self):
        return f"{self.code} ({self.discount_percentage}%)"

    def is_valid(self):
        now = timezone.now() + timedelta(hours=4)

        valid_from = (
            timezone.make_aware(self.valid_from)
            if timezone.is_naive(self.valid_from)
            else self.valid_from
        )
        valid_until = (
            timezone.make_aware(self.valid_until)
            if timezone.is_naive(self.valid_until)
            else self.valid_until
        )

        is_valid = (
            self.is_active
            and (valid_from <= now <= valid_until)
            and (self.used_count < self.usage_limit)
        )

        return is_valid
    

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.user.username} - {self.balance} AZN"

    def deposit(self, amount):
        self.balance += Decimal(amount)
        self.save(update_fields=['balance'])

    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= Decimal(amount)
            self.save(update_fields=['balance'])
            return True
        return False


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.rating}"