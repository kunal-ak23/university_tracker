from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    OEMViewSet, ProgramViewSet, UniversityViewSet, ContractViewSet,
    BatchViewSet, BillingViewSet, PaymentViewSet, ContractFileViewSet,
    StreamViewSet, TaxRateViewSet, LoginView, RegisterView, UserViewSet,
    InvoiceViewSet, DashboardViewSet, StudentViewSet, ChannelPartnerViewSet,
    ChannelPartnerProgramViewSet, ChannelPartnerStudentViewSet, ProgramBatchViewSet
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
router.register(r'students', StudentViewSet)
router.register(r'channel-partners', ChannelPartnerViewSet)
router.register(r'channel-partner-programs', ChannelPartnerProgramViewSet)
router.register(r'channel-partner-students', ChannelPartnerStudentViewSet)
router.register(r'program-batches', ProgramBatchViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]