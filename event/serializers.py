from rest_framework import serializers
from .models import Event, Ticket, Category, OrderItem, Order, PromoCode, Review
from django.db.models import Avg


class EventNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title'] 


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    event = EventNestedSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'event', 'user', 'rating', 'comment', 'created_at']

    def validate(self, data):
        request = self.context.get('request')
        event_id = request.query_params.get('event')
        user = request.user
        if Review.objects.filter(event_id=event_id, user=user).exists():
            raise serializers.ValidationError("You have already rated this event.")
        return data


class PromoCodeSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.id')

    class Meta:
        model = PromoCode
        fields = '__all__'
        read_only_fields = ('used_count', 'created_by')


class TicketModelSerializer (serializers. ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id',
            'event',
            'event_title',
            'name',
            'price',
            'current_price',
            'discount_percentage',
            'quantity_avaible',
        ]


class CategoryModelSerializer (serializers. ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class EventListModelSerializer (serializers. ModelSerializer):
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ['id', 'title', 'date', 'venue', 'language', 'average_rating']
        read_only_fields = ['id']

    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return round(avg, 2) if avg is not None else None


class EventModelSerializer (serializers. ModelSerializer):
    category = CategoryModelSerializer(many=True, read_only=True)
    tickets = TicketModelSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ['id',
                'title',
                'description',
                'date',
                'venue',
                'language',
                'is_active',
                'organizer',
                'category',
                'tickets',]
        

class OrderItemModelSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'ticket', 'price', 'quantity', 'order']

    def create(self, validated_data):
        ticket = validated_data['ticket']
        quantity = validated_data['quantity']
        order = validated_data['order']

        if ticket.quantity_avaible < quantity:
            raise serializers.ValidationError(
                f"Only {ticket.quantity_avaible} tickets available for '{ticket.event} - {ticket.name}' tickets."
            )

        ticket.quantity_avaible -= quantity
        ticket.save()

        validated_data['price'] = ticket.price

        order_item = super().create(validated_data)

        return order_item
    

class OrderModelSerializer(serializers.ModelSerializer):
    orderitems = OrderItemModelSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'orderitems', 'total_price', 'promo_code', 'discount_amount', 'final_price', 'status', 'ordered_at', 'confirmed_at', 'updated_at', 'customer']
    
    def get_total_price(self, obj):
        return obj.total_price