from rest_framework import viewsets
from .models import (
    OEM, Course, University, Stream, Contract, ContractCourse, Batch,
    Billing, Payment, ContractFile, TaxRate
)
from .serializers import (
    OEMSerializer, CourseSerializer, UniversitySerializer, StreamSerializer, ContractSerializer,
    ContractCourseSerializer, BatchSerializer, BillingSerializer, PaymentSerializer,
    ContractFileSerializer, TaxRateSerializer
)
from .permissions import IsProviderPOC, IsUniversityPOC

class OEMViewSet(viewsets.ModelViewSet):
    queryset = OEM.objects.all()
    serializer_class = OEMSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

class UniversityViewSet(viewsets.ModelViewSet):
    queryset = University.objects.all()
    serializer_class = UniversitySerializer

class StreamViewSet(viewsets.ModelViewSet):
    queryset = Stream.objects.all()
    serializer_class = StreamSerializer
    permission_classes = [IsProviderPOC]

class ContractViewSet(viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsUniversityPOC]

class ContractCourseViewSet(viewsets.ModelViewSet):
    queryset = ContractCourse.objects.all()
    serializer_class = ContractCourseSerializer

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer

class BillingViewSet(viewsets.ModelViewSet):
    queryset = Billing.objects.all()
    serializer_class = BillingSerializer

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

class ContractFileViewSet(viewsets.ModelViewSet):
    queryset = ContractFile.objects.all()
    serializer_class = ContractFileSerializer

class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer