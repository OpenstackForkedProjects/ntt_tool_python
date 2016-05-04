from rest_framework import serializers
from models import *


class CloudSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cloud
        exclude = ('creator', 'updated_on')


class TrafficSerializer(serializers.ModelSerializer):
    test_method = serializers.SerializerMethodField()

    class Meta:
        model = Traffic
        exclude = ('creator', 'updated_on',)

    def get_test_method(self, obj):
        test_methods = {"icmp": False, "tcp": False, "udp": False}
        for test_method in obj.test_method.split(","):
            test_methods[test_method] = True
        return test_methods


class TrafficListSerializer(serializers.ModelSerializer):
    test_method = serializers.SerializerMethodField()

    class Meta:
        model = Traffic
        exclude = ('creator', 'updated_on',)

    def get_test_method(self, obj):
        test_methods = {"icmp": False, "tcp": False, "udp": False}
        for test_method in obj.test_method.split(","):
            test_methods[test_method] = True
        return test_methods


class TenantListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ('id', 'tenant_id', 'tenant_name', 'enabled', 'is_selected')


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        exclude = ('creator', 'created_on', 'updated_on',)


class SubnetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subnet


class NetworkSerializer(serializers.ModelSerializer):
    subnets = SubnetSerializer(many=True, read_only=True)

    class Meta:
        model = Network
        exclude = ('creator', 'created_on', 'updated_on',)


class EndpointSerializer(serializers.ModelSerializer):
    network_id = serializers.IntegerField(source='network.id', read_only=True)
    network_name = serializers.CharField(source="network.network_name", read_only=True)

    class Meta:
        model = Endpoint
        fields = ('id', 'network_id', 'network_name', 'endpoint_id', 'name', 'status', 'ip_address', 'is_selected')


class UDPTestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = UDPTestResults


class ICMPTestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ICMPTestResults


class TCPTestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCPTestResults


class TestRunSerializer(serializers.ModelSerializer):
    udp_test_results = UDPTestResultSerializer(many=True, read_only=True)
    icmp_test_results = ICMPTestResultSerializer(many=True, read_only=True)
    tcp_test_results = TCPTestResultSerializer(many=True, read_only=True)

    class Meta:
        model = TestRun
        depth = 1


class TestRunListSerializer(serializers.ModelSerializer):
    traffic_name = serializers.CharField(source='traffic.name', read_only=True)

    class Meta:
        model = TestRun