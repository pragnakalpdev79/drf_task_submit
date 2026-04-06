# Standard Library Imports
import logging

# Third-Party Imports (Django)
from django.shortcuts import render
from django.contrib.auth.models import Group,Permission
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework import generics,status,viewsets,filters
from rest_framework.permissions import AllowAny,IsAuthenticated,IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

# Local Imports
from .models import CustomUser,address
from .serializers import *


logger = logging.getLogger('user')

#===============================================================================================
#===============================================================================================
# USER-RELAYTED VIEWS
# 1.REGISTRATION - Allowany
# 2.LOGIN - Allowany
# 3.LOGOUT - Logged in user only
# 4. DELETE USER VIEW -Admin only
# 5. RESTORE USER VIEW - Admin Only

#============================================================
# 1.REGISTRATION - Allowany
@extend_schema_view(
    post=extend_schema(
        summary=" U.1 Sign-Up",
        description=" Endpoint for new user registration of all types.",
        tags=["Userbase"],
    ))
class UserRegisterationView(generics.CreateAPIView):
    """
    API endpoint for new user registration.
    generics.CreateAPIView inherits from APIView
    Extends with mixin CreateModelMixin
    Specifcialy to handle create_only post method handler
    only works with post requests
    """
    serializer_class = CustomUserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self,request,*args,**kwargs):
        """
        API endpoint for new user registration.post request with details 
        """
        logger.info(" Create function intiated ")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        logger.info(" Serialzer validation successful ")
        user = serializer.save()
        logger.info(" Serialzer save successful")
        refresh = RefreshToken.for_user(user)
        logger.info("p2.4 token generation successful` ")
        perm_user = CustomUser.objects.get(email=user.email)

        if user.check_if_customer:
            group = Group.objects.get(name='Customers')
            perm_user.groups.add(group)
            logger.info(f" {group}==>{perm_user}")

        if user.check_if_restaurant:
            group = Group.objects.get(name='RestrauntOwners')
            perm_user.groups.add(group)
            logger.info(f" {group}==>{perm_user}")

        if user.check_if_driver:
            group = Group.objects.get(name='Drivers')
            perm_user.groups.add(group)
            logger.info(f" {group}==>{perm_user}")

        logger.info(f"{perm_user} added to group {group}")

        return Response( {
            'user' : serializer.data.get("email"),
            'message' : f"You have been successfully registered as a {group}",
            'refresh' : str(refresh),
            'access' : str(refresh.access_token),
        },status=status.HTTP_201_CREATED
        )







#============================================================
# 2.LOGIN - Allowany
@extend_schema_view(
    post=extend_schema(
        summary=" U.2 Login",
        description="Registered users login here",
        tags=["Userbase"],
    ))
class UserLoginView(APIView):
    """
    Endpoint created using APIView as it only serves one function
    of logging in the user hence modelviewset is not used here
    """
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = CustomUserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = RefreshToken.for_user(serializer.validated_data['user'])
        return Response({
            'user' : serializer.validated_data['email'],
            'refresh' : str(refresh),
            'access' : str(refresh.access_token),
        },status=status.HTTP_201_CREATED)







#============================================================
# 3.LOGOUT - Logged in user only
@extend_schema_view(
    post=extend_schema(
        summary=" U.3 Logout",
        description="Logged-in users logout here",
        tags=["Userbase"],
    ))
class UserLogoutView(APIView):
    """
    Endpoint created using APIView as it only serves one function
    of logging out the user hence modelviewset is not used here
    """
    permission_classes = [IsAuthenticated]

    def post(self,request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
        
            return Response({
                'message' : 'Log out successful',
            },status=status.HTTP_205_RESET_CONTENT)
        
        except Exception as e:
            logger.info(f"An error occured in log out == {e}")
            return Response({
                'error' : 'something went wrong'
            },status=status.HTTP_400_BAD_REQUEST)






#============================================================
# 4. DELETE USER VIEW -Admin only
@extend_schema_view(
    delete=extend_schema(
        summary=" Delete User",
        description=" U.4 Admin only feature to soft deleted user",
        tags=["Admin-Only"],
    ))
class DeleteUser(APIView):
    """
    Endpoint to delete existing user from main user base
    only admin has the permission to access this endpoint
    """
    queryset = CustomUser
    permission_classes = [IsAdminUser] 
    def delete(self,request,uname):
        if uname is not None:
            try:
                user = CustomUser.objects.get(username=uname)
            except CustomUser.DoesNotExist:
                logger.info("D1. -- The requested user does not exist")
                return Response({
                    "error" : "The Requested User does not exist" 
                })
           
            user.delete()
        logger.info("D1.2-USER FOUND AND DELETED ")
        return Response({
            'message' : 'User has been deleted',
        })






#============================================================
# 5. RESTORE USER VIEW - Admin Only
@extend_schema_view(
    post=extend_schema(
        summary=" U.5 Restore User",
        description=" Admin only feature to restore soft deleted users",
        tags=["Admin-Only"],
    ))
class RestoreDeletedUserView(APIView):
    """
    Endpoint to restore deleted user from main user base
    only admin has the permission to access this endpoint
    """
    permission_classes = [IsAdminUser]

    def post(self,request,uname):
        if uname is not None:
            try:
                user = CustomUser.all_objects.get(username=uname)
            
            except CustomUser.DoesNotExist:
                logger.info("R1.1 - RESTORE REQUEST USER DOES NOT EXISTS")
                return Response({
                    "error" : "The Requested User does not exist" 
                })
            user.restore()
        logger.info("R1.2-USER FOUND AND DELETED ")
        
        return Response({
            'message' : 'User has been restored',
        })
    
#===============================================================================================
#===============================================================================================

