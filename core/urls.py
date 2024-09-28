from rest_framework.routers import DefaultRouter
from .views import (
    OEMViewSet, CourseViewSet, UniversityViewSet, ContractViewSet,
    ContractCourseViewSet, BatchViewSet, BillingViewSet, PaymentViewSet, ContractFileViewSet
)

router = DefaultRouter()
router.register(r'oems', OEMViewSet)
router.register(r'courses', CourseViewSet)
router.register(r'universities', UniversityViewSet)
router.register(r'contracts', ContractViewSet)
router.register(r'contract-courses', ContractCourseViewSet)
router.register(r'batches', BatchViewSet)
router.register(r'billings', BillingViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'contract-files', ContractFileViewSet)

urlpatterns = router.urls