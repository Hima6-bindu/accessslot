"""
Health check endpoint for deployment monitoring.

This endpoint is public (no authentication required) and is used by
Render and other deployment platforms to verify the service is running.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db import connection


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Public health check endpoint.
    
    Returns HTTP 200 with basic status information.
    Does not require authentication.
    
    Verifies:
    - Django application is running
    - Database connection is working
    
    Returns:
        JSON response with status information
    """
    health_status = {
        'status': 'ok',
        'service': 'AccessSlot API',
    }
    
    # Check database connectivity
    try:
        connection.ensure_connection()
        health_status['database'] = 'connected'
    except Exception as e:
        health_status['database'] = 'error'
        health_status['database_error'] = str(e)
        return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response(health_status, status=status.HTTP_200_OK)
