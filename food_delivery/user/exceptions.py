# api/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
    NotFound,
    MethodNotAllowed
)
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings
import logging
import traceback
import os

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Comprehensive exception handler for DRF.
    Provides consistent, user-friendly error responses.
    """
    # Call DRF's default exception handler for handling common exceptions such as validation and permission
    response = exception_handler(exc, context)
    
    # Request object
    request = context.get('request')

#CODE FOR PRODUCTION AND SHORT WITH TRACEBACK RESPONSE
    # if response is not None:
    #     # os.system('clear')
    #     if settings.DEBUG:
    #         print("debug!--")
    #         error_details = {
    #             'message' : str(exc),
    #             'traceback' : traceback.format_exc() if hasattr(exc,'__traceback__') else None,
    #             'context' : {
    #                 'view' : context.get('view').__class__.__name__ if context.get('view') else None,
    #                 'request_method' : context.get('request').method if context.get('request') else None,
    #             }
    #         }
    #     else:
    #         print("creating custom response")
    #         error_details = {
    #             'message' : get_error_message(response.status_code,exc) if 'get_error_message' in globals() else 'An error occured',
    #             'code' : 'error'
    #         }
    #     print("creating custom response")
    #     custom_response_data = {
    #         'success' : False,
    #         'error' : {
    #             'status_code' : response.status_code,
    #             **error_details,
    #             'type' : exc.__class__.__name__,
    #         }
    #     }
    #     print(custom_response_data)
    #     response.data = custom_response_data
    #     return response
    
#CUSTOM EXCPETION HANDLER FOR USER-FRIENDLY ERROR MESSAGES
    if response is not None:
        # Customize based on exception type
        error_data = {
            'success': False,
            'error': {}
        }
        
        # Authentication errors
        if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            error_data['error'] = {
                'status_code': 401,
                'message': 'Authentication required hello!!!!',
                'details': {
                    'code': 'authentication_required',
                    'hint': 'Include a valid token in Authorization header: Bearer <token>'
                }
        }
        # Permission errors
        elif isinstance(exc, PermissionDenied):
            error_data['error'] = {
                'status_code': 403,
                'message': 'Permission denied',
                'details': {
                    'code': 'permission_denied',
                    'hint': 'You do not have permission to perform this action'
                }
            }
        # JWT token errors
        elif isinstance(exc, (InvalidToken, TokenError)):
            error_data['error'] = {
                'status_code': 401,
                'message': 'Invalid or expired token',
                'details': {
                    'code': 'token_error',
                    'hint': 'Get a new token at /api/token/ or refresh at /api/token/refresh/'
                }
            }        
        # Validation errors
        elif isinstance(exc, ValidationError):
            formatted_errors = format_validation_errors(response.data)
            error_data['error'] = {
                'status_code': 400,
                'message': 'Validation failed',
                'details': {
                    'code': 'validation_error',
                    'fields': formatted_errors
                }
            }
        
        # Not found errors
        elif isinstance(exc, NotFound):
            error_data['error'] = {
                'status_code': 404,
                'message': 'Resource not found',
                'details': {
                    'code': 'not_found',
                    'hint': 'The requested resource does not exist'
                }
            }
        
        # Method not allowed
        elif isinstance(exc, MethodNotAllowed):
            error_data['error'] = {
                'status_code': 405,
                'message': 'Method not allowed',
                'details': {
                    'code': 'method_not_allowed',
                    'allowed_methods': exc.allowed_methods if hasattr(exc, 'allowed_methods') else []
                }
            }
        
        # Generic error
        else:
            error_data['error'] = {
                'status_code': response.status_code,
                'message': get_error_message(response.status_code),
                'details': response.data if settings.DEBUG else {'code': 'error'}
            }
        
        error_data['error']['type'] = exc.__class__.__name__
        
        # Log error
        logger.error(
            f"Error {error_data['error']['status_code']}: {exc}",
            extra= {
                'request_path': request.path if request else None,
                'request_method': request.method if request else None,
            },
            exc_info=settings.DEBUG
        )
        
        response.data = error_data
        print(response.data)
    
    else:
        error_data = {
            'success': False,
            'error': {
                'status_code': 500,
                'message': 'Internal server error',
                'details': {
                    'code': 'server_error',
                    'message': str(exc) if settings.DEBUG else 'An unexpected error occurred'
                },
                'type': exc.__class__.__name__
            }
        }
        logger.exception(f"Unexpected error: {exc}")
        response = Response(error_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response

def format_validation_errors(errors):
    formatted = {}
    
    if isinstance(errors, dict):
        for field, field_errors in errors.items():
            if isinstance(field_errors, list):
                formatted[field] = field_errors[0] if field_errors else 'Invalid value'
            elif isinstance(field_errors, dict):
                formatted[field] = format_validation_errors(field_errors)
            else:
                formatted[field] = str(field_errors)
    
    return formatted

def get_error_message(status_code):
    messages = {
        400: 'Bad request',
        401: 'Authentication required',
        403: 'Permission denied',
        404: 'Resource not found',
        405: 'Method not allowed',
        429: 'Too many requests',
        500: 'Internal server error',
    }
    return messages.get(status_code, 'An error occurred')