import django_filters
from user.models import *

#==============================================================================
# MENU ITEM FILTER
class MenuItemFilter(django_filters.FilterSet):
    restaurant = django_filters.NumberFilter()
    category = django_filters.CharFilter()
    dietary_info = django_filters.CharFilter()
    is_available = django_filters.BooleanFilter()
    price__lte = django_filters.NumberFilter(field_name='price',lookup_expr='lte')

    class Meta:
        model = MenuItem
        fields = ['restaurant','category','dietary_info','is_available']

#==============================================================================
# ORDER FILTER
class OrderFilter(django_filters.FilterSet):
    status = django_filters.CharFilter()
    restaurant = django_filters.NumberFilter()
    created_at__gte = django_filters.DateTimeFilter(field_name='created_at',lookup_expr='gte')

    class Meta:
        model = Order
        fields = ['status','restaurant']

#==============================================================================
# REVIEW FILTER
class ReviewFilter(django_filters.FilterSet):
    rating = django_filters.NumberFilter()
    restaurant = django_filters.NumberFilter()
    menu_item = django_filters.NumberFilter()

    class Meta:
        model = Review
        fields = ['rating','restaurant','menu_item']
