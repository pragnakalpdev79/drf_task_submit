from rest_framework.pagination import LimitOffsetPagination,PageNumberPagination
from rest_framework.response import Response

class RestoPagination(PageNumberPagination):
    page_size = 20

class MenuItemPagination(PageNumberPagination):
    page_size = 30


class Testlistlspagination(LimitOffsetPagination):
    default_limit = 1
    limit_query_param = 'limit'
    offset_query_param = 'offset'
    max_limit = 100