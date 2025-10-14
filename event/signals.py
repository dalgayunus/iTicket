from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Event
from .models import Ticket
from .models import Category
from .models import Wallet
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def create_wallet_for_user(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)

@receiver(post_save, sender=Event)
def inform_about_new_event(sender, instance, created, **kwargs):
    if created:
        print('New event is created with title: ', instance.title)
    else:
        print('New event is updated with title: ', instance.title)


@receiver(pre_save, sender=Ticket)
def validate_ticket_price(sender, instance, **kwargs):
    price = instance.price
    if price < 0:
        raise ValueError('Ticket price can not be negative')

@receiver(pre_save, sender=Ticket)
def validate_ticket_quantity(sender, instance, **kwargs):
    quantity_avaible = instance.quantity_avaible
    if quantity_avaible < 0:
        raise ValueError('Ticket quantity can not be negative')


@receiver(post_save, sender=Category)
def inform_about_new_category(sender, instance, created, **kwargs):
    if created:
        print('New category is created with name: ', instance.name)
    else:
        print('New category is updated with name: ', instance.name)
        

@receiver(pre_save, sender=Category)
def validate_category_name(sender, instance, **kwargs):
    if Category.objects.filter(name=instance.name).exclude(id=instance.id).exists():
        raise ValueError('Category name already exists')