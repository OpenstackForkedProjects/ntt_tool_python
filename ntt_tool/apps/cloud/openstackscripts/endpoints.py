import json
import time
from netaddr import IPRange
from django.db import transaction
from neutronclient.v2_0 import client as neutron_client
from novaclient.v1_1 import client as nova_client
from ntt_tool.apps.cloud.models import Network, Endpoint
from credentials import *
from novaclientutils import NovaClientUtils


class DiscoverEndpoints(object):

    def __init__(self, traffic, network):
        self.traffic = traffic
        self.network = network
        self.neutron = neutron_client.Client(**get_credentials(self.traffic.cloud))
        self.nova = nova_client.Client(**get_nova_credentials(self.traffic.cloud))

    def get_endpoints(self, subnet):
        ip_range = IPRange(subnet.ip_range_start, subnet.ip_range_end)
        ports = self.neutron.list_ports(network_id=self.network.network_id).get('ports')
        endpoints = []
        with transaction.atomic():
            filters = {
                "traffic_id": self.traffic.id,
                "network_id": self.network.id,
            }
            Endpoint.objects.filter(**filters).update(is_dirty=False)
            for port in ports:
                if port.get("device_owner") in ["compute:compute", "compute:nova"]:
                    if port['fixed_ips'][0]['subnet_id'] == subnet.subnet_id:
                        endpoint = self.nova.servers.get(port['device_id'].encode('unicode_escape'))
                        if endpoint and endpoint.status == 'ACTIVE':
                            ip_address = port['fixed_ips'][0]['ip_address'].encode('unicode_escape')
                            if ip_address in ip_range:
                                endpoint_obj, created = Endpoint.objects.get_or_create(traffic_id=self.traffic.id,
                                                                                       network_id=self.network.id,
                                                                                       endpoint_id=endpoint.id)
                                endpoint_obj.name = endpoint.name
                                endpoint_obj.ip_address = ip_address
                                endpoint_obj.status = endpoint.status
                                endpoint_obj.is_dirty = True
                                endpoint_obj.save()
                                endpoints.append(endpoint_obj)
            Endpoint.objects.filter(**filters).filter(is_dirty=False).delete()
        return endpoints


class LaunchEndpoints(NovaClientUtils):

    def __init__(self, **credentials):
        super(LaunchEndpoints, self).__init__(**credentials)

    def launch_endpoints(self, request, traffic):
        endpoints = []
        with transaction.atomic():
            Network.objects.filter(tenant__traffic_id=traffic.id).update(is_selected=False)
            for selected_network in json.loads(request.data.get("json", '[]')):
                network = Network.objects.get(pk=selected_network.get("network_id"))
                network.is_selected = True
                network.endpoint_count = selected_network.get("endpoint_count")
                network.save()

                endpoint_name = "-".join([network.tenant.tenant_name,
                                          network.network_name,
                                          time.strftime("%Y%m%d%H%M%S")])
                launched_endpoints = self.launch_endpoint(network.tenant.tenant_id,
                                                          network.network_id,
                                                          endpoint_name,
                                                          network.endpoint_count)
                filters = {
                    "traffic_id": traffic.id,
                    "network_id": network.id,
                }
                Endpoint.objects.filter(**filters).update(is_dirty=False)
                for endpoint in launched_endpoints:
                    endpoint_obj, created = Endpoint.objects.get_or_create(traffic_id=traffic.id,
                                                                           network_id=network.id,
                                                                           endpoint_id=endpoint.id)
                    endpoint_obj.name = endpoint.name
                    endpoint_obj.ip_address = endpoint.addresses.get(network.network_name)[0].get("addr")
                    endpoint_obj.status = endpoint.status
                    endpoint_obj.is_dirty = True
                    endpoint_obj.save()
                    endpoints.append(endpoint_obj)
                Endpoint.objects.filter(**filters).filter(is_dirty=False).delete()
        return endpoints
