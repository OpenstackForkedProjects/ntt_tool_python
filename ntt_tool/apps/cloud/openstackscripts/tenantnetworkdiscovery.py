import logging
from django.db import transaction
from django.utils import timezone
# from neutronclientutils import NeutronClientUtils
from ntt_tool.apps.cloud.models import Tenant, Network, Subnet
# from ntt_tool.apps.cloud.serializers import TenantSerializer


logger = logging.getLogger(__name__)


class TenantsController(object):

    def __init__(self, traffic_id):
        self.traffic_id = traffic_id

    def save(self, creator, tenants):
        """
        Updating/Saving tenants in NTTT database.
        """
        discovery_datetime = timezone.now()
        with transaction.atomic():
            Tenant.objects.filter(traffic_id=self.traffic_id).update(is_dirty=False)

            tenant_objs = []
            for tenant in tenants:
                filters = {
                    "tenant_id": tenant.id,
                    "traffic_id": self.traffic_id
                }
                tenant_obj, created = Tenant.objects.get_or_create(**filters)
                tenant_obj.tenant_name = tenant.name
                tenant_obj.description = tenant.description
                tenant_obj.enabled = tenant.enabled
                tenant_obj.creator = creator
                tenant_obj.is_dirty = True
                tenant_obj.updated_on = discovery_datetime
                tenant_obj.save()
                tenant_objs.append(tenant_obj)

            # Deleting tenants which are got deleted in openstack
            Tenant.objects.filter(traffic_id=self.traffic_id)\
                .filter(is_dirty=False).delete()

            return tenant_objs


class NetworkController(object):

    def save(self, neutron_utils, creator, tenant, networks):
        discovery_datetime = timezone.now()

        with transaction.atomic():
            # Making tenant as selected.
            Tenant.objects.filter(traffic_id=tenant.traffic.id)\
                .update(is_selected=False)
            tenant.is_selected = True
            tenant.save()

            Network.objects.filter(tenant_id=tenant.id).update(is_dirty=False)

            network_objs = []
            for network in networks.get("networks", []):
                filters = {
                    "tenant_id": tenant.id,
                    "network_id": network.get('id')
                }
                network_obj, created = Network.objects.get_or_create(**filters)
                network_obj.network_name = network.get('name')
                network_obj.shared = network.get('shared')
                network_obj.status = network.get('status')
                network_obj.is_dirty = True
                network_obj.creator = creator
                network_obj.created_on = discovery_datetime
                network_obj.updated_on = discovery_datetime
                network_obj.save()
                network_objs.append(network_obj)

                # Setting all records belongs to tenant as not dirty/updated
                Subnet.objects.filter(network_id=network_obj.id)\
                    .update(is_dirty=False)

                subnets = neutron_utils.list_subnets(network_id=network_obj.network_id)
                for subnet in subnets.get("subnets", []):
                    filters = {
                        "network_id": network_obj.id,
                        "subnet_id": subnet.get("id")
                    }
                    subnet_obj, created = Subnet.objects.get_or_create(**filters)
                    subnet_obj.subnet_name = subnet.get("name")
                    subnet_obj.cidr = subnet.get("cidr")
                    subnet_obj.allocation_pool_start = subnet.get("allocation_pools")[0].get("start")
                    subnet_obj.allocation_pool_end = subnet.get("allocation_pools")[0].get("end")
                    subnet_obj.is_dirty = True
                    subnet_obj.save()

                # Deleting subnets which are got changed after discovery
                Subnet.objects.filter(network_id=network_obj.id)\
                    .filter(is_dirty=False).delete()

            # Deleting networks which are not got deleted in openstack during discovery
            Network.objects.filter(tenant_id=tenant.id)\
                .filter(is_dirty=False).delete()

            return network_objs

# class NetworkSubnetDiscovery(NeutronClientUtils):
#
#     def get_networks_and_subnets(self, user, cloud_id, tenants):
#         # neutron = self.get_client_instance()
#
#         discovery_result = []
#         with transaction.atomic():
#             discovery_datetime = timezone.now()
#
#             Tenant.objects.filter(cloud_id=cloud_id)\
#                 .update(is_dirty=False)
#
#             for tenant in tenants:
#                 tenant_obj = None
#                 try:
#                     tenant_obj = Tenant.objects.filter(tenant_id=tenant.id).get()
#                 except Tenant.DoesNotExist:
#                     tenant_obj = Tenant()
#                 tenant_obj.cloud_id = cloud_id
#                 tenant_obj.tenant_id = tenant.id
#                 tenant_obj.tenant_name = tenant.name
#                 tenant_obj.description = tenant.description
#                 tenant_obj.enabled = tenant.enabled
#                 tenant_obj.creator = user
#                 tenant_obj.is_dirty = True
#                 tenant_obj.updated_on = discovery_datetime
#                 tenant_obj.save()
#
#                 # Setting all records belongs to tenant as not dirty/updated
#                 Network.objects.filter(tenant__tenant_id=tenant.id)\
#                     .update(is_dirty=False)
#
#                 networks = self.list_networks(tenant_id=tenant.id)
#                 for network in networks.get("networks", []):
#                     network_obj = None
#                     try:
#                         filters = {
#                             "tenant__tenant_id": tenant.id,
#                             "network_name": network.get("name")
#                         }
#                         network_obj = Network.objects.filter(**filters).get()
#                     except Network.DoesNotExist:
#                         network_obj = Network()
#                     network_obj.tenant = tenant_obj
#                     network_obj.network_id = network.get("id")
#                     network_obj.network_name = network.get("name")
#                     network_obj.shared = network.get("shared")
#                     network_obj.status = network.get("status")
#                     network_obj.is_dirty = True
#                     network_obj.creator = user
#                     network_obj.updated_on = discovery_datetime
#                     network_obj.save()
#
#                     # Setting all records belongs to tenant as not dirty/updated
#                     Subnet.objects.filter(network__network_id=network.get("id"))\
#                         .update(is_dirty=False)
#
#                     subnets = self.list_subnets(network_id=network.get("id"))
#                     for subnet in subnets.get("subnets"):
#                         subnet_obj = None
#                         try:
#                             filters = {
#                                 "network__network_id": network.get("id"),
#                                 "subnet_id": subnet.get("id")
#                             }
#                             subnet_obj = Subnet.objects.filter(**filters).get()
#                         except Subnet.DoesNotExist:
#                             subnet_obj = Subnet()
#                         subnet_obj.subnet_id = subnet.get("id")
#                         subnet_obj.network_id = network_obj.id
#                         subnet_obj.subnet_name = subnet.get("name")
#                         subnet_obj.cidr = subnet.get("cidr")
#                         subnet_obj.is_dirty = True
#                         subnet_obj.save()
#
#                     # Deleting subnets which are got changed after discovery
#                     Subnet.objects.filter(network__network_id=network.get("id"))\
#                         .filter(is_dirty=False).delete()
#
#                 # Deleting networks which are not got changed after discovery
#                 Network.objects.filter(tenant__tenant_id=tenant_obj.id)\
#                     .filter(is_dirty=False).delete()
#
#                 serializer = TenantSerializer(tenant_obj)
#                 discovery_result.append(serializer.data)
#
#             # Deleting tenants which are got changed after discovery
#             Tenant.objects.filter(cloud_id=cloud_id)\
#                 .filter(is_dirty=False).delete()
#         return discovery_result
