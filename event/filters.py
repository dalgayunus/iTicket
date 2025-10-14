from django_filters import rest_framework as filters
from .models import Event, Ticket


class EventFilter(filters.FilterSet):
    title = filters.CharFilter(field_name='title', lookup_expr='icontains')
    venue = filters.CharFilter(field_name='venue', lookup_expr='icontains')
    date_after = filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_before = filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    category = filters.NumberFilter(field_name='category__id', lookup_expr='exact')
    language = filters.CharFilter(field_name='language', lookup_expr='exact')
    is_active = filters.BooleanFilter(field_name='is_active')
    
    class Meta:
        model = Event
        fields = []

    
class TicketFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = filters.NumberFilter(field_name='price', lookup_expr='lte')
    event_id = filters.NumberFilter(field_name='event__id', lookup_expr='exact')
    event_title = filters.CharFilter(field_name='event__title', lookup_expr='icontains')
    quantity = filters.BooleanFilter(method='filter_quantity', label='Is ticket avaible')
    
    class Meta:
        model = Ticket
        fields = []

    def filter_quantity(self, queryset, name, value):
        if value is True:
            return queryset.filter(quantity_avaible__gt=0)
        if value is False:
            return queryset.filter(quantity_avaible__lte=0)
        return queryset