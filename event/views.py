from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Event, Category, Ticket, Order, OrderItem, PromoCode, Review, Wallet
from .serializers import EventListModelSerializer, EventModelSerializer, OrderItemModelSerializer, OrderModelSerializer, PromoCodeSerializer, ReviewSerializer
from .serializers import TicketModelSerializer
from .serializers import CategoryModelSerializer
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import action
from rest_framework import permissions, status
from django_filters import rest_framework as filters
from rest_framework import filters as drf_filters
from .paginators import CustomPageNumberPagination
from .permissions import (
    CanManageEvents, 
    CanApplyDiscount, 
    CanManageTickets, 
    CanManageCategories,
    IsOrganizerOrAdmin,
    IsCustomerOrAdmin
)
from .filters import EventFilter, TicketFilter
from django.http import FileResponse
from .utils import generate_ticket_pdf, send_ticket_email
import os
from django.db import transaction
from django.db.models import F
import decimal
from decimal import Decimal
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone


class HealthCheckAPIView(APIView):
    def get(self, request):
        return Response({'status':'ok'})
    

class EventViewSet (viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventModelSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageEvents]
    filter_backends = [filters.DjangoFilterBackend, drf_filters.SearchFilter, drf_filters.OrderingFilter]
    search_fields = ['title', 'description', 'venue', 'category__name']
    ordering_fields = ['title', 'date', 'venue']
    ordering = ['date']
    pagination_class = CustomPageNumberPagination
    filterset_class = EventFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return EventListModelSerializer
        return EventModelSerializer

    def get_queryset(self):
        venue = self.request.query_params.get('venue')
        if venue:
            return self.queryset.filter(venue=venue)
        return super().get_queryset()
    
    def get_permissions(self):

        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [permissions.IsAuthenticated]

        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOrganizerOrAdmin]

        else:
            permission_classes = self.permission_classes
        
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'], url_path='change_title')
    def change_title(self, request, pk=None): 
        event = self.get_object() 
        new_title = request.data.get('title') 
        serializer = self.get_serializer(event, {'title':new_title}, partial=True) 
        serializer.is_valid(raise_exception=True) 
        serializer.save() 
        return Response({'message': 'Event name changed successfully', 'event': EventModelSerializer(event).data})


class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketModelSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageTickets]
    search_fields = ['event__title']
    ordering_fields = ['event_title', 'name', 'price', 'current_price', 'discount_percentage']
    ordering = ['price']
    filterset_class = TicketFilter

    def get_permissions(self):

        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [permissions.IsAuthenticated]

        else:
            permission_classes = [permissions.IsAuthenticated, CanManageTickets]
        
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'], url_path='discount')
    def apply_discount(self, request, pk=None):
        ticket = self.get_object()
        discount_percentage = request.data.get('discount_percentage', 0)
        ticket.current_price = ticket.price * decimal.Decimal(1-discount_percentage/100)
        ticket.discount_percentage = discount_percentage
        ticket.save()
        return Response({'message': 'Discount applied successfully', 'ticket': TicketModelSerializer(ticket).data})

    @action(detail=False, methods=['get'], url_path='most_discounted_tickets')
    def order_most_discounted_tickets(self, request):
        tickets = self.queryset.order_by('-discount_percentage')
        return Response(self.get_serializer(tickets, many=True).data)
    
    @action(detail=True, methods=['post'], url_path='change_name')
    def change_name(self, request, pk=None): 
        ticket = self.get_object() 
        new_name = request.data.get('name') 
        serializer = self.get_serializer(ticket, {'name':new_name}, partial=True) 
        serializer.is_valid(raise_exception=True) 
        serializer.save() 
        return Response({'message': 'Ticket name changed successfully', 'ticket': TicketModelSerializer(ticket).data})
    
    @action(detail=True, methods=['post'], url_path='change_event')
    def change_event(self, request, pk=None):
        ticket = self.get_object()
        new_event_id = request.data.get('event_id')

        if not new_event_id:
            return Response({'error': 'event_id is required'}, status=400)

        try:
            event = Event.objects.get(id=new_event_id)
        except Event.DoesNotExist:
            return Response({'error': 'Event not found'}, status=404)

        serializer = self.get_serializer(ticket, {'event': event.id}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'message': 'Ticket event changed successfully', 'ticket': TicketModelSerializer(ticket).data})
    

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategoryModelSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageCategories]

    def get_permissions(self):

        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated, CanManageCategories]
        
        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'], url_path='update_name')
    def update_name(self, request, pk=None):
        category = self.get_object()
        new_name = request.data.get('name')
        serializer = self.get_serializer(category, {'name':new_name}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': 'Category name updated successfully','category': CategoryModelSerializer(category).data})
    
    @action(detail=False, methods=['get'], url_path='by_name')
    def by_name(self, request):
        category = self.queryset.order_by('name')
        return Response(self.get_serializer(category, many=True).data)


class OrderItemAPIView(APIView):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemModelSerializer
    permission_classes = [IsCustomerOrAdmin]

    def post(self, request):
        wallet = request.user.wallet
        order = Order.objects.create(customer=request.user)
        data = request.data.copy()

        if isinstance(data, dict):
            data = [data]
        elif isinstance(data, str):
            import json
            data = json.loads(data)

        for item in data:
            item['order'] = order.id

        serializer = self.serializer_class(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        order_items = serializer.save()

        total_cost = 0

        for order_item in order_items:
            ticket = order_item.ticket
            total_cost += ticket.current_price * order_item.quantity


        return Response({'message': 'Order created successfully', 
                         'total_spent': float(total_cost),
                         'order items':serializer.data})


class OrderAPIView(APIView):
    queryset = Order.objects.all()
    serializer_class = OrderModelSerializer
    permission_classes = [IsCustomerOrAdmin]

    def get(self, request, pk=None):
        if pk:
            order = self.queryset.get(id=pk)

            if order.customer != request.user:
                return Response({'message': 'You are not authorized to view this order'}, status=status.HTTP_403_FORBIDDEN)
            return Response(self.serializer_class(order).data)
                 

        orders = self.queryset.filter(customer=request.user)
        return Response(self.serializer_class(orders, many=True).data)
    
    def patch(self, request, pk=None):
        try:
            order = self.queryset.get(id=pk)
        except Order.DoesNotExist:
            return Response({'message': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if order.customer != request.user:
            return Response({'message': 'You are not authorized to update this order'}, status=status.HTTP_403_FORBIDDEN)

        previous_status = order.status
        serializer = self.serializer_class(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        wallet = request.user.wallet

        if previous_status != 'cancelled' and order.status == 'cancelled':
            refund_amount = order.final_price or order.total_price or Decimal('0.00')
            wallet.deposit(refund_amount)

            return Response({
                'message': f'Order cancelled. {refund_amount} AZN refunded to wallet.',
                'wallet_balance': wallet.balance
            })

        if previous_status != 'confirmed' and serializer.data['status'] == 'confirmed':

            total_cost = order.final_price or order.total_price or Decimal('0.00')

            if wallet.balance < total_cost:
                order.status = 'pending'
                order.save()
                return Response({
                    'error': 'Your balance is not enough.'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                wallet.balance -= total_cost
                wallet.save()

            for order_item in order.orderitems.all():
                promo_code_str = getattr(order.promo_code, 'code', None)
                discount_amount = order.discount_amount
                final_price = order.final_price

                pdf_path = generate_ticket_pdf(
                    order_item,
                    promo_code_str,
                    discount_amount,
                    final_price
                )
                send_ticket_email(order_item, pdf_path)

                return Response({
                'message': f'Order confirmed. {total_cost} AZN has been deducted from your balance and tickets have been sent.',
                'wallet_balance': wallet.balance
            })

        return Response({'message': 'Order updated successfully', 'order': serializer.data})
    

class PromoCodeViewSet(viewsets.ModelViewSet):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer

    def get_permissions(self):
        if self.action in ['list', 'create', 'retrieve', 'update', 'partial_update', 'destroy']:
            return [IsOrganizerOrAdmin()]
        if self.action == 'check':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=['post'])
    def check(self, request):
        code = request.data.get('code')
        if not code:
            return Response({'valid': False, 'message': 'Promo code not sent.'}, status=400)
        try:
            promo = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            return Response({'valid': False, 'message': 'Code not found.'}, status=404)

        if promo.is_valid():
            return Response({'valid': True, 'discount': promo.discount_percentage})
        return Response({'valid': False, 'message': 'Promo code is invalid.'}, status=400)
    

class ApplyPromoAPIView(APIView):
    permission_classes = [IsCustomerOrAdmin]

    def post(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'message': 'Order not found.'}, status=404)

        if order.customer != request.user and request.user.role != 'admin':
            return Response({'message': 'You cannot process this order.'}, status=403)

        if order.status == 'confirmed':
            return Response({'message': 'Promo codes cannot be applied to confirmed orders.'}, status=400)
        
        if order.status == 'cancelled':
            return Response({'message': 'Promo codes cannot be applied to canceled orders.'}, status=400)

        if order.promo_code:
            return Response({'message': 'Promo code has already been applied to this order.'}, status=400)

        code = request.data.get('code')
        if not code:
            return Response({'message': 'Code not sent.'}, status=400)

        try:
            promo = PromoCode.objects.get(code=code)
        except PromoCode.DoesNotExist:
            return Response({'message': 'Promo code not found.'}, status=404)
        
        for item in order.orderitems.all():
            if item.ticket.event.date < timezone.now():
                return Response({'message': 'Promo codes cannot be applied to events that have already ended.'}, status=400)

        if not promo.is_valid():
            return Response({'message': 'The promo code is invalid or the limit has been reached.'}, status=400)

        total = order.total_price
        discount = (total * promo.discount_percentage) / Decimal('100.00')

        with transaction.atomic():
            updated = PromoCode.objects.filter(pk=promo.pk, used_count__lt=promo.usage_limit).update(used_count=F('used_count')+1)
            if updated == 0:
                return Response({'message': 'The promo code usage limit has expired.'}, status=400)

            order.discount_amount = discount.quantize(Decimal('0.01'))
            order.promo_code = promo
            order.final_price = (total - order.discount_amount).quantize(Decimal('0.01'))
            order.save()

        return Response({
            'message': f'Promo code applied: -{promo.discount_percentage}%',
            'new_total': str(order.final_price),
            'discount_amount': str(order.discount_amount)
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wallet_balance(request):
    wallet = request.user.wallet
    return Response({
        "balance": float(wallet.balance)
    })


class AddBalanceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required'}, status=400)
        
        try:
            amount = Decimal(amount)
        except:
            return Response({'error': 'Invalid amount'}, status=400)
        
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        wallet.balance += amount
        wallet.save()

        return Response({'balance': wallet.balance})


class TicketPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            order_item = OrderItem.objects.get(id=pk, order__customer=request.user)
            order = order_item.order
            promo_code = order.promo_code
            discount_amount = order.discount_amount
            final_price = order.final_price
        except OrderItem.DoesNotExist:
            return Response({'error': 'Ticket not found or access denied'}, status=404)

        file_path = generate_ticket_pdf(order_item, promo_code, discount_amount, final_price)
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))


class ReviewListCreateAPIView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        event_id = self.request.query_params.get('event')
        serializer.save(user=self.request.user, event_id=event_id)

    def get_queryset(self):
        event_id = self.request.query_params.get('event')
        if event_id:
            return self.queryset.filter(event_id=event_id)
        return self.queryset