import django_filters
from user.models import *

#==============================================================================
# RESTAURANT FILTER
class RestoFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains') #lookup_expr='icontains' means "contains" (case-insensitive)
    cuisine_type = django_filters.CharFilter()
    is_open = django_filters.BooleanFilter()
    delivery_fee__lte = django_filters.NumberFilter(field_name='delivery_fee',lookup_expr='lte')
    minimum_order__lte = django_filters.NumberFilter(field_name='minimum_order',lookup_expr='lte')
    average_rating__gte = django_filters.NumberFilter(field_name='average_rating',lookup_expr='gte')

    class Meta:
        model = RestrauntModel
        fields = ['name','cuisine_type','is_open']
