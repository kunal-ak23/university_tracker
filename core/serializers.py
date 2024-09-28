from rest_framework import serializers

from .models import (
    OEM, Course, University, Contract, ContractCourse, Batch,
    Billing, Payment, ContractFile, Stream, TaxRate
)

# OEM Serializer
class OEMSerializer(serializers.ModelSerializer):
    class Meta:
        model = OEM
        fields = '__all__'


# Course Serializer
class CourseSerializer(serializers.ModelSerializer):
    provider = OEMSerializer(read_only=True)
    provider_id = serializers.PrimaryKeyRelatedField(queryset=OEM.objects.all(), source='provider', write_only=True)

    class Meta:
        model = Course
        fields = '__all__'


# University Serializer
class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'


# ContractCourse Serializer
class ContractCourseSerializer(serializers.ModelSerializer):
    course = CourseSerializer(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), source='course', write_only=True)

    class Meta:
        model = ContractCourse
        fields = '__all__'


class StreamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stream
        fields = '__all__'

# Contract Serializer
class ContractSerializer(serializers.ModelSerializer):
    stream = StreamSerializer(read_only=True)
    stream_id = serializers.PrimaryKeyRelatedField(queryset=Stream.objects.all(), source='stream', write_only=True)
    contract_courses = ContractCourseSerializer(many=True, read_only=True)
    contract_files = serializers.FileField(allow_null=True, required=False)

    class Meta:
        model = Contract
        fields = '__all__'


# Batch Serializer
class BatchSerializer(serializers.ModelSerializer):
    contract_course = ContractCourseSerializer(read_only=True)
    contract_course_id = serializers.PrimaryKeyRelatedField(queryset=ContractCourse.objects.all(), source='contract_course', write_only=True)

    class Meta:
        model = Batch
        fields = '__all__'


# Billing Serializer
class BillingSerializer(serializers.ModelSerializer):
    batch = BatchSerializer(read_only=True)
    batch_id = serializers.PrimaryKeyRelatedField(queryset=Batch.objects.all(), source='batch', write_only=True)
    total_payments = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance_due = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Billing
        fields = '__all__'


# Payment Serializer
class PaymentSerializer(serializers.ModelSerializer):
    billing = BillingSerializer(read_only=True)
    billing_id = serializers.PrimaryKeyRelatedField(queryset=Billing.objects.all(), source='billing', write_only=True)

    class Meta:
        model = Payment
        fields = '__all__'


# ContractFile Serializer
class ContractFileSerializer(serializers.ModelSerializer):
    contract = ContractSerializer(read_only=True)
    contract_id = serializers.PrimaryKeyRelatedField(queryset=Contract.objects.all(), source='contract', write_only=True)

    class Meta:
        model = ContractFile
        fields = '__all__'

class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = '__all__'