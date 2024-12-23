from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    OEMViewSet, ProgramViewSet, UniversityViewSet, ContractViewSet,
    ContractProgramViewSet, BatchViewSet, BillingViewSet, PaymentViewSet, 
    ContractFileViewSet, RegisterView, UserProfileView,
    StreamViewSet, TaxRateViewSet, UserViewSet
)
from .auth import CustomLoginView

# Auth endpoints
urlpatterns = [
    # Auth endpoints
    path('auth/login/', CustomLoginView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/me/', UserProfileView.as_view(), name='user_profile'),

    # Model endpoints
    path('oems/', OEMViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('oems/<int:pk>/', OEMViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    
    path('programs/', ProgramViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('programs/<int:pk>/', ProgramViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    
    path('universities/', UniversityViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('universities/<int:pk>/', UniversityViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    
    path('contracts/', ContractViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('contracts/<int:pk>/', ContractViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
    
    path('contract-programs/', ContractProgramViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('contract-programs/<int:pk>/', ContractProgramViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    
    path('batches/', BatchViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('batches/<int:pk>/', BatchViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    
    path('billings/', BillingViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('billings/<int:pk>/', BillingViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    
    path('payments/', PaymentViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('payments/<int:pk>/', PaymentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    
    path('contract-files/', ContractFileViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('contract-files/<int:pk>/', ContractFileViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    })),
    
    path('streams/', StreamViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('streams/<int:pk>/', StreamViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    
    path('tax-rates/', TaxRateViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('tax-rates/<int:pk>/', TaxRateViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    
    path('users/', UserViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })),
    path('users/<int:pk>/', UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })),
]