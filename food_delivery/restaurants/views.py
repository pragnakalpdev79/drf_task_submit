# Standard Library Imports
import logging

# Third-Party Imports (Django)
from django.core.cache import cache
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema,extend_schema_view
from rest_framework import generics,status,viewsets,filters
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny,IsAuthenticatedOrReadOnly,IsAuthenticated
from rest_framework.response import Response

# Local Imports
from user.models import *
from user.permissions import IsRestaurantOwner
from .serializers import *
from .pagination import RestoPagination,MenuItemPagination
from .filters import RestoFilter
from orders.filters import MenuItemFilter

logger = logging.getLogger('user')


#============================================================
# 1.RESTAURANTS VIEWSET 
@extend_schema_view(
    list=extend_schema(
        summary=" R.1 List of all restaurants",
        description="You can get a list of all restaurants available here",
        tags=["Restaurants"],
        responses=RestoListSerializer,
        auth=[],
    ),
    retrieve=extend_schema(
        summary=" R.2 Get details of a restaurant",
        description="Pass the restaurant id to get all details about it",
        tags=["Restaurants"],
        auth=[],
    ),
    create=extend_schema(
        summary="R.3 Register Your restaurant",
        description="Enter your restaurant details and register a new one,this endpoint can be only accesed if you are a restaurnt owner" \
        " [Restaurant Owner Permission Required]",
        tags=["Restaurants"],
        auth=[{"tokenAuth": [], }],
    ),
    menu=extend_schema(
        summary=" R.4 Get Menu from a restaurant id",
        description="Pass Restaurant id to get its menu",
        tags=["Restaurants"],
        auth=[],
    ),
    popular=extend_schema(
        summary=" R.5 Check popular restaurants",
        description="Endpoint to fetch popular restaurants ordered by top rated",
        tags=["Restaurants"],
        auth=[],
    ),
    deleter=extend_schema(
        summary=" R.6 Delete a restaurant",
        description="Can be only accessed if user has restaurant owner permission",
        tags=["Restaurants"],
        auth=[{"tokenAuth": [], }],
    ),
    partial_update=extend_schema(
        summary=" R.7 Update restaurant details",
        description="Can be only accessed if user has restaurant owner permission",
        tags=["Restaurants"],
        auth=[{"tokenAuth": [], }],
    )
)
class RestaurantViewSet(viewsets.ModelViewSet):
    """
    RESTAURANT MANAGEMENT VIEWSET
    HAS FOLLOWING FUNCTIONS
    1. LIST ALL
    2. GET BY ID
    3. REGISTER NEW FOR OWNERS
    4. GET MENU BY RESTAURANT ID
    5. GET POPULAR RESTAURANTS
    6. DELETE YOUR RESTAURANT
    7. UPDATE RESTAURANT DETAILS
    """
    queryset = RestrauntModel.objects.filter(deleted_at=None).annotate(items_count=Count('menu'))
    http_method_names = ['get', 'post','patch']
    pagination_class = RestoPagination
    filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    search_fields = ['name','cuisine_type','description']
    ordering_fields = ['average_rating','delivery_fee','created_at']
    ordering = ['-average_rating']
    filterset_class = RestoFilter

    def get_serializer_class(self):
        logger.info(self.action)
        if self.action == 'list':
            return RestoListSerializer
        elif self.action == 'create':
            return RestoCreateSerializer
        elif self.action == 'retrieve':
            return RestoSerializer
        elif self.action == 'menu':
            return MenuItemSerializer
        elif self.action == "partial_update":
            return RestoUpdateSerializer

        print("none")
        return RestoListSerializer
    
    def get_permissions(self):
        print(self.action)
        if self.action == 'list':
            return [AllowAny()]
        if self.action == 'create':
            logger.info("Create action detected")
            return [IsRestaurantOwner()]
        if self.action == 'deleter':
            return [IsRestaurantOwner()]
        return [IsAuthenticatedOrReadOnly()]
    
#==============================================================================
# 1. GET ALL RESTAURANTS BY GET METHOOD
    def list(self,request):
        if request.version == 'v2':
            logger.info("using v2")
            cache_key = 'resto_list'
            cached_data = cache.get(cache_key)
            print(type(cached_data))
            if cached_data is None:
                logger.info("not cached yet")
                queryset = self.filter_queryset(self.get_queryset())
                page = self.paginate_queryset(queryset)
                if page is not None:
                    print(page)
                    serializer = self.get_serializer(page,many=True)
                    cached_data = serializer.data
                    cache.set(cache_key,cached_data,300)
                    return self.get_paginated_response(serializer.data)
                
            return Response(cached_data)
        # by defualt v1
        logger.info("using v1")
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            logger.info(page)
            serializer = self.get_serializer(page,many=True)
            logger.info(f"returning {self.get_paginated_response(serializer.data)}")
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset,many=True)
        logger.info(f"Listing all rests : -  {type(serializer.data)}")
        return Response(serializer.data)


    
#==============================================================================
# 2. GET ONE RESTAURANT BY ITS ID
    def retrieve(self, request, pk=None):
        if request.version == 'v2':
            logger.info("using v2")
            cache_key = f"resto_{pk}"
            cached_data = cache.get(cache_key)
            if cached_data is None:
                resto = RestrauntModel.objects.prefetch_related('menu','review_for').get(id=pk)
                serializer = self.get_serializer(resto)
                cached_data = serializer.data
                cache.set(cache_key,cached_data,600)
                return Response({
                    "message" : "Here are the restaurant details",
                    "resto_id" : pk,
                    'details' : serializer.data,
                })
            return Response(cached_data)
        resto = RestrauntModel.objects.prefetch_related('menu','review_for').get(id=pk)
        serializer = self.get_serializer(resto)
        return Response({
            "message" : "Here are the restaurant details",
            "resto_id" : pk,
            'details' : serializer.data,
        })
#==============================================================================
# 3. REGISTER A NEW RESTAURANT - BY OWNER ONLY
    def create(self,request,*args,**kwargs):
        logger.info(request.user.has_perm("add_restrauntmodel"))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
            'success': True,
            'message' : "Your restaurant has been successfully registered with us",
            'data' : serializer.data,
        },
        status=status.HTTP_201_CREATED)

# 3.1 ACTUAL MODEL SAVE FOR NEW RESTO + CACHE INVALIDATION
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        cache.delete('resto_list')
        cache.delete('popular_restos')
        logger.info("cache cleared after new restaurant")

#==============================================================================
# 4. GET MENU ITEMS OF A SPECIFC RESTAURANT IF YOU HAVE RESTO ID
    @action(detail=True,methods=['get'],
            pagination_class=MenuItemPagination)
    def menu(self,request,pk=None):
        queryset = MenuItem.objects.filter(restaurant_id=pk)
        self.filterset_class = MenuItemFilter
        self.search_fields = ['name','description']
        self.ordering_fields = ['price','name','created_at']
        self.ordering = ['name']
        queryset = self.filter_queryset(queryset)
    
        if request.version == 'v2':
            logger.info("using v2")
            cache_key = f"menuof__{pk}"
            cached_data = cache.get(cache_key)
            if cached_data is None:
                logger.info("not cached yet")
                page = self.paginate_queryset(queryset)
                if page is not None:
                    serializer = self.get_serializer(page,many=True)
                    cached_data = serializer.data
                    cache.set(cache_key,cached_data,900)
                    return self.get_paginated_response(serializer.data)
            return Response(cached_data)
        logger.info("using v1")
        page = self.paginate_queryset(queryset)

        if page is not None:
            logger.info("p1")
            serializer = self.get_serializer(page,many=True)
            return self.get_paginated_response(serializer.data)
    
        serializer = self.get_serializer(queryset,many=True)
        logger.info("listing all menu items")

        if not serializer.data:
            msg = "The requested menu does not exist"
            st = status.HTTP_404_NOT_FOUND
        else:
            msg = "Here is the menu for restaurant"
            st = status.HTTP_200_OK

        return Response({
            "message" : msg,
            "id": pk,
            "menu" : serializer.data,
        },
        status = st)
    
#==============================================================================
# 5. POPULAR RESTOS - CACHED 30 MIN
    @action(detail=False,methods=['get'])
    def popular(self,request):
        cache_key = 'popular_restos'
        cached = cache.get(cache_key)

        if cached:
            logger.info("returning cached popular restos")
            return Response(cached)
        
        queryset = RestrauntModel.objects.order_by('-total_reviews')
        serializer = self.get_serializer(queryset,many=True)
        cache.set(cache_key,serializer.data,1800)  # 30 minutes
        logger.info("listing popular restos and caching")
        return Response(serializer.data)

#==============================================================================
# 6. DELETE A RESTO + CACHE INVALIDATION
    @action(detail=True,methods=['delete'])
    def deleter(self,request,pk):
        print(request.user)
        resto = self.get_queryset().get(id=pk)
        if resto.owner != request.user:
            return Response({
                "error" : "not allowed",
            },status = status.HTTP_403_FORBIDDEN)
        print(type(resto))
        resto.delete()
        cache.delete('resto_list')
        cache.delete(f'resto_{pk}')
        cache.delete(f'menuof__{pk}')
        cache.delete('popular_restos')
        logger.info("cache cleared after restaurant delete")
        return Response({"message" : request.user.email})

#==============================================================================
# 7. UPDATE RESTAURANT - CACHE INVALIDATION ON PATCH

    def partial_update(self,request,pk=None):
        instance = self.get_object()
        logger.info(f"min_order {instance.minimum_order} ")
        serializer = self.get_serializer(instance,data=request.data,partial=True)
        serializer.is_valid(raise_exception=True)
        logger.info("hello")    
        #logger.info(serializer.data)
        self.perform_update(serializer)
        return Response({
            "message" : "Works",
            "requested" : pk,
            'data': serializer.data,
        })

    def perform_update(self,serializer):
        logger.info(serializer)
        logger.info(serializer.validated_data)
        instance = serializer.save()
        cache.delete('resto_list')
        cache.delete(f'resto_{instance.pk}')
        cache.delete('popular_restos')
        logger.info(f"cache cleared after restaurant update {instance.pk}")


#==============================================================================
#==============================================================================
# MENU ITEM VIEWSET

@extend_schema_view(
    list=extend_schema(
        summary=" M.1 List menu items",
        description="List all menu items for the restaurant owner",
        tags=["Menu Items"],
        auth=[{"tokenAuth": [], }],
    ),
    create=extend_schema(
        summary=" M.2 Add new menu item",
        description="Add a new menu item to your restaurant",
        tags=["Menu Items"],
        auth=[{"tokenAuth": [], }],
    ),
    partial_update=extend_schema(
        summary=" M.3 Update menu item",
        description="Update details of a menu item",
        tags=["Menu Items"],
        auth=[{"tokenAuth": [], }],
    ),
)
class MenuItemViewSet(viewsets.ModelViewSet):
    """
    MENU-ITEM VIEWSET
    HAS FOLLOWING FUNCTIONS
    1. CREATE
    2. UPDATE
    3. DELETE
    """

    permission_classes = [IsRestaurantOwner]
    filterset_class = MenuItemFilter
    filter_backends = [DjangoFilterBackend,filters.SearchFilter,filters.OrderingFilter]
    search_fields = ['name','description']
    ordering_fields = ['price','name','created_at']
    ordering = ['name']
    #http_method_names = ['get', 'post','patch']

    def get_serializer_class(self):
        logger.info(self.action)
        if self.action == 'list':
            return MenuListSerializer
        elif self.action == 'create':
            return MenuSerializer
        elif self.action == "partial_update":
            return MenuUSerializer

    def get_queryset(self):
        qs = MenuItem.objects.all()
        if self.action == 'list':
            resto = RestrauntModel.objects.filter(owner_id=self.request.user).first()
            test = qs.filter(restaurant=resto)
            return test
        if self.action == 'create':
            return qs
    
    #post/CREATE MENU - ITEMS
#WORKS    
    def create(self,request):
        print("post request!")
        serializer = self.get_serializer(data=request.data)
        logger.info(" C.3 applying validation")
        serializer.is_valid(raise_exception=True)
        logger.info("validation done")
        self.perform_create(serializer)

        return Response({
            "message": "Menu item added successfully",
            "email": request.user.email,
            "Added": serializer.validated_data,
        },status=status.HTTP_201_CREATED)

#WORKS
    def perform_create(self,serializer):
        mid = serializer.validated_data.pop('restoid')
        print(mid)
        serializer.save(restaurant_id=mid)
        cache.delete(f'menuof__{mid}')
        cache.delete('resto_list')
        logger.info(f"cache cleared after new menu item for resto {mid}")
#PATCH-PARTIAL_UPDATE

    def partial_update(self, request, pk=None):
        logger.info("update called")
        print(pk)
        try:
            item = MenuItem.objects.get(id=pk)
        except MenuItem.DoesNotExist:
            return Response({
                "error": "Menu-Item not found"
            },status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(item,data=request.data,partial=True)
        logger.info("Serializer called")
        logger.info(serializer)
        serializer.is_valid(raise_exception=True)
        logger.info("validated")
        self.perform_update(serializer)
        return Response({
            "message" : "A Patch request"
        })

    def perform_update(self,serializer):
        logger.info("In perform update")
        #mid = serializer.validated_data.pop('restoid')
        
        instance = serializer.save()
        cache.delete(f'menuof__{instance.restaurant_id}')
        cache.delete(f'resto_{instance.restaurant_id}')
        logger.info(f"cache cleared after menu item update {instance.pk}")

    def perform_destroy(self,instance):
        resto_id = instance.restaurant_id
        instance.delete()
        cache.delete(f'menuof__{resto_id}')
        cache.delete(f'resto_{resto_id}')
        logger.info(f"cache cleared after menu item delete")
