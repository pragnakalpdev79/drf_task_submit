from rest_framework.throttling import UserRateThrottle

class OrderCreateT(UserRateThrottle):
    rate = '20/hour'

class ReviewCreateT(UserRateThrottle):
    rate = '10/hour'    

class LocationUp(UserRateThrottle):
    rate = '500/hour'