import random 
from rest_framework import throttling


class Ordercreation(throttling.BaseThrottle):
    def allow_request(self, request, view):
        return super().allow_request(request, view)
