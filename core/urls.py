from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OEMViewSet, ProgramViewSet, UniversityViewSet, ContractViewSet,
    BatchViewSet, BillingViewSet, PaymentViewSet, ContractFileViewSet,
    StreamViewSet, TaxRateViewSet, LoginView, RegisterView, UserViewSet,
    InvoiceViewSet, DashboardViewSet
)

router = DefaultRouter()
router.register(r'oems', OEMViewSet)
router.register(r'programs', ProgramViewSet)
router.register(r'universities', UniversityViewSet)
router.register(r'contracts', ContractViewSet)
router.register(r'batches', BatchViewSet)
router.register(r'billings', BillingViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'contract-files', ContractFileViewSet)
router.register(r'streams', StreamViewSet)
router.register(r'tax-rates', TaxRateViewSet)
router.register(r'users', UserViewSet)
router.register(r'invoices', InvoiceViewSet)
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
]