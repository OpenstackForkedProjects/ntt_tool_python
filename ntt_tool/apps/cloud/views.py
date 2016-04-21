import json
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from models import *
from serializers import *
from openstackscripts.keystoneclientutils import KeystoneClientUtils
from openstackscripts.novaclientutils import NovaClientUtils
from openstackscripts.tenantnetworkdiscovery import *
from openstackscripts.credentials import *
from openstackscripts.endpoints import DiscoverEndpoints, LaunchEndpoints
from openstackscripts.traffictest.traffictest import TrafficTest

import os
import pickle
from django.core.mail import EmailMultiAlternatives
from django.template import Context
from django.template.loader import get_template
from django.template.loader import render_to_string


from django.core.mail import EmailMessage
from email.mime.text import MIMEText
from django.conf import settings


class CloudViewSet(viewsets.ModelViewSet):
    queryset = Cloud.objects.all()
    serializer_class = CloudSerializer
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    action_serializers = {
        'retrieve': TenantSerializer,
        'list': TenantSerializer,
        'create': TenantSerializer,
        'update': TenantSerializer,
    }

    def get_serializer_class(self):
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]
        return super(TrafficViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        cloud_id = self.request.GET.get("cloud_id")
        queryset = self.filter_queryset(
                Tenant.objects.filter(cloud_id=cloud_id))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=["get"], url_path="discover/(?P<cloud_id>[^/.]+)")
    def discover(self, request, cloud_id=None):
        cloud = None
        try:
            cloud = Cloud.objects.get(pk=cloud_id, creator=request.user)
        except Cloud.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        keystone_utils = KeystoneClientUtils(**get_credentials(cloud))
        tenants = keystone_utils.get_tenants()

        network_subnets_discovery = NetworkSubnetDiscovery(**get_credentials(cloud))
        tenant_networks_routers = network_subnets_discovery.get_networks_and_subnets(
                request.user,
                cloud_id,
                tenants
        )
        return Response(tenant_networks_routers)


class TrafficViewSet(viewsets.ModelViewSet):
    queryset = Traffic.objects.all()
    serializer_class = TrafficSerializer
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    action_serializers = {
        'retrieve': TrafficRetrieveSerializer,
        'list': TrafficListSerializer,
        'create': TrafficSerializer,
        'update': TrafficSerializer,
    }

    def get_serializer_class(self):
        """
        Overriding method to get custom serializer classes based on request method.
        """
        if hasattr(self, 'action_serializers'):
            if self.action in self.action_serializers:
                return self.action_serializers[self.action]
        return super(TrafficViewSet, self).get_serializer_class()

    def list(self, request, *args, **kwargs):
        """
        Overriding list method to write custom queryset for retriveing traffic related to cloud.
        """
        cloud_id = self.request.GET.get("cloud_id")
        queryset = self.filter_queryset(
                Traffic.objects.filter(cloud_id=cloud_id))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        Overriding method to retriveing only traffic info for edit and get related info for view traffic.
        """
        instance = self.get_object()
        if json.loads(request.GET.get('get_related_data', 'false')):
            serializer = self.get_serializer(instance)
        else:
            serializer = TrafficSerializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """
        Overriding method to provide selected tenants, creator and cloud_id at the time of creating traffic.
        """
        serializer.save(
            tenants=self.request.data.getlist("tenants[]"),
            creator=self.request.user,
            cloud_id=self.request.data.get("cloud_id")
        )

    @detail_route(methods=["get"], url_path="select/tenant/(?P<tenant_id>[-\w]+)")
    def select_tenant(self, request, pk=None, tenant_id=None):
        """
        Method provides the functionality to select a tenant for traffic.
        """
        with transaction.atomic():
            tenant = Tenant.objects.filter(tenant_id=tenant_id).get()

            traffic = Traffic.objects.get(pk=pk)
            traffic.tenants.clear()
            traffic.selected_networks.clear()
            traffic.tenants.add(tenant)
            traffic.save()
            TrafficNetworksMap.objects.filter(traffic=traffic).delete()

            serializer = TenantSerializer(tenant)
            return Response(serializer.data)

    @detail_route(methods=["get"], url_path="select/network")
    def select_network(self, request, pk=None):
        """
        Method to select networks for a selected tenant of a traffic.
        """
        with transaction.atomic():
            traffic = Traffic.objects.get(pk=pk)
            if json.loads(request.GET.get("is_selected")):
                network = Network.objects.get(pk=request.GET.get("network_id"))
                traffic_network_map, created = TrafficNetworksMap.objects.get_or_create(traffic=traffic, network=network)
                traffic_network_map.save()

                # Subnet id of the first subnet of a network
                subnet_obj = network.subnets.all()[0]
                neutron_utils = NeutronClientUtils(**get_credentials(traffic.cloud))
                subnet = neutron_utils.show_subnet(subnet_id=subnet_obj.subnet_id)
                subnet_obj.allocation_pool_start = subnet.get("allocation_pools")[0].get("start")
                subnet_obj.allocation_pool_end = subnet.get("allocation_pools")[0].get("end")
                subnet_obj.save()

                serializer = SubnetSerializer(subnet_obj)
                return Response(serializer.data)

            TrafficNetworksMap.objects.filter(traffic=traffic)\
                .filter(network_id=request.GET.get("network_id")).delete()
        return Response(status.HTTP_200_OK)

    @detail_route(methods=["get"], url_path="endpoints")
    def endpoints(self, request, pk=None):
        """
        Lists all the endpoints belongs to a specific network of a traffic.
        """
        endpoints = Endpoint.objects.filter(traffic_id=pk)
        serializer = EndpointSerializer(endpoints, many=True)
        return Response(serializer.data)

    @detail_route(methods=["post"], url_path="endpoints/discover")
    def discover_endpoints(self, request, pk=None):
        """
        Discovers the endpoints from openstack environment for selected networks with given IP range of a traffic.
        """
        response = []
        selected_networks = []
        for selected_range in json.loads(request.data.get("json", '[]')):
            network_id = selected_range.get("network_id")
            selected_networks.append(network_id)
            filters = {
                "traffic_id": pk,
                "network_id": network_id
            }
            obj = TrafficNetworksMap.objects.filter(**filters).get()
            obj.ip_range_start = selected_range.get("ip_range_start")
            obj.ip_range_end = selected_range.get("ip_range_end")
            obj.save()

            endpoint_discovery = DiscoverEndpoints(pk, network_id)
            endpoints = endpoint_discovery.get_endpoints(obj.ip_range_start, obj.ip_range_end)
            response.extend(endpoints)

        # Deleting endpoints for unselected networks (If selected previously and unselected in current request)
        Endpoint.objects.filter(traffic_id=pk).exclude(network_id__in=selected_networks).delete()

        serializer = EndpointSerializer(response, many=True)
        return Response(serializer.data)

    @detail_route(methods=["post"], url_path="endpoints/launch")
    def launch_endpoints(self, request, pk=None):
        response = []
        traffic = Traffic.objects.get(pk=pk)
        nova_credentials = get_nova_credentials(traffic.cloud)

        selected_networks = []
        for selected_item in json.loads(request.data.get("json", '[]')):
            network_id = selected_item.get("network_id")
            selected_networks.append(network_id)
            filters = {
                "traffic_id": pk,
                "network_id": network_id
            }
            obj, created = TrafficNetworksMap.objects.get_or_create(**filters)
            obj.endpoint_count = selected_item.get("endpoint_count")
            obj.save()

            launch_endpoint = LaunchEndpoints(traffic, network_id, **nova_credentials)
            endpoints = launch_endpoint.launch(selected_item.get("endpoint_count"))
            response.extend(endpoints)

        # Deleting endpoints for unselected networks (If selected previously and unselected in current request)
        Endpoint.objects.filter(traffic_id=pk).exclude(network_id__in=selected_networks).delete()

        serializer = EndpointSerializer(response, many=True)
        return Response(serializer.data)

    @detail_route(methods=["get"], url_path="endpoints/select")
    def select_endpoint(self, request, pk=None):
        filters = {
            "traffic_id": pk,
            "endpoint_id": request.GET.get("endpoint_id")
        }
        endpoint = Endpoint.objects.filter(**filters).get(pk=request.GET.get("endpoint_pk"))
        endpoint.is_selected = json.loads(request.GET.get("is_selected"))
        endpoint.save()

        serializer = EndpointSerializer(endpoint)
        return Response(serializer.data)

    @detail_route(methods=["get"], url_path="run/test")
    def run_traffic_test(self, request, pk=None):
        traffic_test = TrafficTest(pk)
        test_result = traffic_test.run_test()
        return Response(test_result)

    @detail_route(methods=["get"], url_path="email/report")
    def email_report(self, request, pk=None):
        context = None
        file_path = os.path.join(settings.MEDIA_ROOT, "traffic-test-report.txt")
        with open(file_path, 'r') as f:
            test_result = pickle.load(f)  # load file content as mydict
            context = Context({
                'test_result': test_result,
                'reciever_name': request.user.username,
            })

        sender = settings.EMAIL_HOST_USER
        message = get_template('email_templates/traffic_test_report.html').render(context)
        msg = EmailMessage("Traffic Test Report", message, to=['abdulgaffar@onecloudinc.com', request.user.email], from_email=sender)
        msg.content_subtype = 'html'

        f = file(file_path, 'rb')
        attachment = MIMEText(f.read())
        attachment.add_header('Content-Disposition', 'attachment', filename="traffic-test-report.txt")
        msg.attach(attachment)
        msg.send()
        return Response(True)

