from rest_framework import permissions
from django.contrib.auth import get_user_model
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.conf import settings
import os
import qrcode
import uuid
from django.core.mail import EmailMessage

User = get_user_model()

def send_ticket_email(order_item, pdf_path):
    subject = "🎟️ iTicket - Your Ticket Confirmation"
    message = f"Hi {order_item.order.customer.username},\n\nYour order has been successfully completed!\nYour ticket has been added.\n\nThank you!"
    email = EmailMessage(
        subject,
        message,
        to=[order_item.order.customer.email]
    )
    email.attach_file(pdf_path)
    email.send()


def generate_ticket_pdf(order_item, promo_code=None, discount_amount=None, final_price=None):

    tickets_dir = os.path.join(settings.MEDIA_ROOT, 'tickets')
    os.makedirs(tickets_dir, exist_ok=True)

    file_path = os.path.join(tickets_dir, f"ticket_{order_item.id}.pdf")
    c = canvas.Canvas(file_path, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 20)
    c.drawString(200, height - 100, "✓ iTicket - Event Ticket")

    c.setFont("Helvetica", 14)
    c.drawString(100, height - 160, f"Event: {order_item.ticket.event.title}")
    c.drawString(100, height - 190, f"Venue: {order_item.ticket.event.venue}")
    c.drawString(100, height - 220, f"Date: {order_item.ticket.event.date.strftime('%Y-%m-%d %H:%M')}")
    c.drawString(100, height - 260, f"Ticket: {order_item.ticket.name}")
    c.drawString(100, height - 290, f"Price: {order_item.ticket.price} AZN")
    c.drawString(100, height - 320, f"Quantity: {order_item.quantity}")
    c.drawString(100, height - 350, f"Total price: {order_item.quantity * order_item.ticket.price}")
    c.drawString(100, height - 380, f"Promo code: {promo_code}")
    c.drawString(100, height - 410, f"Discount_amount: {discount_amount}")
    c.drawString(100, height - 440, f"Final price: {final_price}")
    c.drawString(100, height - 490, f"Customer: {order_item.order.customer.username}")
    c.drawString(100, height - 520, f"Status: {order_item.order.status}")


    c.setFont("Helvetica-Oblique", 12)
    c.drawString(100, height - 570, "Please bring this ticket to the event entrance.")

    qr_data = f"TicketID:{order_item.id}|Order:{order_item.order.id}|User:{order_item.order.customer.username}|UUID:{uuid.uuid4()}"
    qr = qrcode.make(qr_data)
    qr_path = os.path.join(tickets_dir, f"qr_{order_item.id}.png")
    qr.save(qr_path)

    qr_size = 150
    c.drawImage(qr_path, 100, 100, qr_size, qr_size)


    c.showPage()
    c.save()
    return file_path


def has_role(user, role):

    if not user or not user.is_authenticated:
        return False
    return user.role == role


def has_any_role(user, roles):

    if not user or not user.is_authenticated:
        return False
    return user.role in roles


def is_admin(user):
    return has_role(user, 'admin')


def is_organizer(user):
    return has_role(user, 'organizer')


def is_customer(user):
    return has_role(user, 'customer')


def is_organizer_or_admin(user):
    return has_any_role(user, ['organizer', 'admin'])


def can_manage_events(user):

    if not user or not user.is_authenticated:
        return False
    
    if user.role == 'admin':
        return True
    elif user.role == 'organizer':
        return True
    elif user.role == 'customer':
        return False
    
    return False


def can_apply_discount(user):

    return is_organizer_or_admin(user)


def can_manage_tickets(user):

    return is_organizer_or_admin(user)


def can_manage_categories(user):

    return is_admin(user)


def get_user_permissions(user):

    if not user or not user.is_authenticated:
        return {
            'can_view_events': False,
            'can_create_events': False,
            'can_update_events': False,
            'can_delete_events': False,
            'can_manage_tickets': False,
            'can_apply_discount': False,
            'can_manage_categories': False,
        }
    
    return {
        'can_view_events': True,
        'can_create_events': is_organizer_or_admin(user),
        'can_update_events': is_organizer_or_admin(user),
        'can_delete_events': is_organizer_or_admin(user),
        'can_manage_tickets': can_manage_tickets(user),
        'can_apply_discount': can_apply_discount(user),
        'can_manage_categories': can_manage_categories(user),
    }