import json
from django.http import HttpResponse
from django.template.loader import get_template
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from ntt_tool.utils.reportutils import render_to_pdf
from serializers import *

from openstackscripts.keystoneclientutils import KeystoneClientUtils
from openstackscripts.neutronclientutils import NeutronClientUtils
from openstackscripts.tenantnetworkdiscovery import *
from openstackscripts.credentials import *
from openstackscripts.endpoints import DiscoverEndpoints, LaunchEndpoints
from openstackscripts.traffictest.traffictest import TrafficTest

from rest_framework import status
import os
import pickle
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


class TrafficViewSet(viewsets.ModelViewSet):
    queryset = Traffic.objects.all()
    serializer_class = TrafficSerializer
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    action_serializers = {
        'retrieve': TrafficSerializer,
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
        cloud_id = self.request.GET.get('cloud_id')
        queryset = self.filter_queryset(
                Traffic.objects.filter(cloud_id=cloud_id))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """
        Overriding method to provide selected tenants, creator and cloud_id at the time of creating traffic.
        """
        serializer.save(
            test_method=self.request.data.get("test_method"),
            creator=self.request.user,
            cloud_id=self.request.data.get('cloud_id')
        )

    def perform_update(self, serializer):
        serializer.save(test_method=self.request.data.get("test_method"))

    @detail_route(methods=['get'], url_path='run/test')
    def run_traffic_test(self, request, pk=None):
        traffic_test = TrafficTest(pk)
        duration = int(request.GET.get('duration'))
        test_result = traffic_test.run_test(request.user, duration=duration)
        return Response(test_result)

    @list_route(methods=['get'], url_path='reports/(?P<pk>[-\w]+)')
    def list_reports(self, request, pk):
        test_runs = TestRun.objects.filter(traffic_id=pk).order_by("-started_on")
        serializer = TestRunListSerializer(test_runs, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'], url_path='report/(?P<test_run_id>[-\w]+)')
    def report(self, request, test_run_id=None):
        test_run = TestRun.objects.get(pk=test_run_id)
        serializer = TestRunSerializer(test_run)
        return Response(serializer.data)

    @list_route(methods=['get', 'post'], url_path='report/download/(?P<test_run_id>[-\w]+)')
    def download_report(self, request, test_run_id=None):
        test_run = TestRun.objects.get(pk=test_run_id)
        serializer = TestRunSerializer(test_run)
        pdf = render_to_pdf('reports/traffic_test_report.html', serializer.data)
        return HttpResponse(pdf.getvalue(), content_type='application/pdf')

    @list_route(methods=['get'], url_path='report/email/(?P<test_run_id>[-\w]+)')
    def email_report(self, request, test_run_id=None):
        test_run = TestRun.objects.get(pk=test_run_id)
        serializer = TestRunSerializer(test_run)
        pdf = render_to_pdf('reports/traffic_test_report.html', serializer.data)

        context = {"user_full_name": request.user.get_full_name()}
        email_content = get_template('email_templates/traffic_test_report.html').render(context)
        mail = EmailMessage("Traffic Test Report",
                            email_content,
                            to=['abdulgaffar@onecloudinc.com', request.user.email, 'keerthiv@onecloudinc.com'],
                            from_email=settings.EMAIL_HOST_USER)
        mail.content_subtype = 'html'
        mail.attach("report.pdf", pdf.getvalue(), 'application/pdf')
        mail.send()
        return Response(True)

    @list_route(methods=["delete"], url_path="report/delete/(?P<test_run_id>[-\w]+)")
    def delete_report(self, request, test_run_id=None):
        TestRun.objects.get(pk=test_run_id).delete()
        return Response(True)


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
        traffic_id = self.request.GET.get("traffic_id")
        queryset = self.filter_queryset(
            Tenant.objects.filter(traffic_id=traffic_id))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=["get"], url_path="discover")
    def discover(self, request):
        cloud = Cloud.objects.get(pk=request.GET.get("cloud_id"), creator=request.user)
        keystone_utils = KeystoneClientUtils(**get_credentials(cloud))
        tenants_ctrl = TenantsController(request.GET.get("traffic_id"))
        tenants = tenants_ctrl.save(request.user, keystone_utils.get_tenants())
        serializer = TenantListSerializer(tenants, many=True)
        return Response(serializer.data)


class NetworkViewSet(viewsets.ModelViewSet):
    queryset = Network.objects.all()
    serializer_class = NetworkSerializer
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        tenant_id = self.request.GET.get("tenant_id")
        networks = Network.objects.filter(tenant_id=tenant_id)

        serializer = self.get_serializer(networks, many=True)
        return Response(serializer.data)

    @list_route(methods=['get'], url_path="discover")
    def discover(self, request):
        tenant = Tenant.objects.get(pk=request.GET.get("tenant_id"))
        neutron_credentials = get_credentials(tenant.traffic.cloud)
        neutron_utils = NeutronClientUtils(**neutron_credentials)
        networks = neutron_utils.list_networks(tenant_id=tenant.tenant_id)

        network_ctrl = NetworkController()
        network_objs = network_ctrl.save(neutron_utils, request.user, tenant, networks)

        serializer = NetworkSerializer(network_objs, many=True)
        return Response(serializer.data)


class EndpointViewSet(viewsets.ModelViewSet):
    queryset = Endpoint.objects.all()
    serializer_class = EndpointSerializer
    authentication_classes = (JSONWebTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = queryset.filter(traffic_id=self.request.GET.get('traffic_id'))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'], url_path='discover/(?P<traffic_id>[-\w]+)')
    def discover(self, request, traffic_id=None):
        endpoints_list = []
        traffic = Traffic.objects.get(pk=traffic_id)

        with transaction.atomic():
            Network.objects.filter(tenant__traffic_id=traffic.id).update(is_selected=False)
            for selected_network in json.loads(request.data.get("json", '[]')):
                network = Network.objects.get(pk=selected_network.get("network_id"))
                network.is_selected = True
                network.save()

                first_subnet = network.subnets.first()
                first_subnet.ip_range_start = selected_network.get("ip_range_start")
                first_subnet.ip_range_end = selected_network.get("ip_range_end")
                first_subnet.save()

                endpoint_discovery = DiscoverEndpoints(traffic, network)
                endpoints = endpoint_discovery.get_endpoints(first_subnet)
                endpoints_list.extend(endpoints)

        serializer = EndpointSerializer(endpoints_list, many=True)
        return Response(serializer.data)

    @list_route(methods=['post'], url_path='launch/(?P<traffic_id>[-\w]+)')
    def launch(self, request, traffic_id=None):
        traffic = Traffic.objects.get(pk=traffic_id)
        nova_credentials = get_nova_credentials(traffic.cloud)
        launch_ep_obj = LaunchEndpoints(**nova_credentials)
        endpoints = launch_ep_obj.launch_endpoints(request, traffic)

        serializer = EndpointSerializer(endpoints, many=True)
        return Response(serializer.data)

    @detail_route(methods=["get"], url_path="select")
    def select(self, request, pk=None):
        endpoint = Endpoint.objects.get(pk=pk)
        endpoint.is_selected = json.loads(request.GET.get("is_selected"))
        endpoint.save()

        serializer = EndpointSerializer(endpoint)
        return Response(serializer.data)
