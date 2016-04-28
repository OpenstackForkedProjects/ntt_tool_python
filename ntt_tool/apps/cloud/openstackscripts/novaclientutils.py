import time
import os
from novaclient.v1_1 import client as nova_client
from novaclient.exceptions import NotFound
from openstackclientutils import OpenStackClientUtils
from keystoneclientutils import KeystoneClientUtils
from glanceclientutils import GlanceClientUtils
from config import *


class NovaClientUtils(OpenStackClientUtils):
    client_class = nova_client.Client

    def __init__(self, **credentials):
        super(NovaClientUtils, self).__init__(**credentials)
        self.nova = self.get_client_instance()

    def assign_floating_ip(self, instance):
        if NOVA_FLOATING_IP_CREATION:
            floating_ip = self.nova.floating_ips.create(NOVA_FLOATING_IP_POOL)
            instance.add_floating_ip(floating_ip)
            return True
        return False

    def launch_endpoint(self, tenant_id, network_id, endpoint_name, min_count=1):
        """
        Launches VM on given tenant and network
        :param tenant_id:
        :param network_id:
        :param endpoint_name:
        :return: VM instance
        """
        self.nova.quotas.update(tenant_id,
                                instances=NOVA_QUOTA_INSTANCES,
                                cores=NOVA_QUOTA_CORES,
                                ram=NOVA_QUOTA_RAM,
                                fixed_ips=NOVA_QUOTA_FIXED_IPS,
                                floating_ips=NOVA_QUOTA_FLOATING_IPS)

        user_data = None
        user_data_file_path = os.path.join(os.path.dirname(__file__), 'user.txt')
        with open(user_data_file_path, 'r') as f:
            user_data = f.read()

        image = None
        try:
            image = self.nova.images.find(name=NOVA_IMAGE_NAME)
        except NotFound:
            # Uploading image if does not exist.
            keystone_credentials = {
                "username": self.credentials.get("username"),
                "password": self.credentials.get("api_key"),
                "auth_url": self.credentials.get("auth_url"),
                "tenant_name": self.credentials.get("project_id")
            }
            keystone = KeystoneClientUtils(**keystone_credentials)
            # ToDo: GLANCE_ENDPOINT is hardcoded. Image will not upload if we select diff network
            glance = GlanceClientUtils(endpoint=GLANCE_ENDPOINT,
                                       token=keystone.get_token())
            image = glance.upload_image()

        # Creating flavor
        flavor = None
        try:
            flavor = self.nova.flavors.find(name=NOVA_VM_FLAVOR)
        except NotFound:
            flavor = self.nova.flavors.create(name=NOVA_VM_FLAVOR,
                                              ram=NOVA_VM_FLAVOR_RAM,
                                              vcpus=NOVA_VM_FLAVOR_VCPUS,
                                              disk=NOVA_VM_FLAVOR_DISK)

        # Launching endpoints
        first_instance = self.nova.servers.create(name=endpoint_name,
                                                  image=image,
                                                  flavor=flavor,
                                                  key_name="admin",
                                                  nics=[{'net-id': network_id}],
                                                  userdata=user_data,
                                                  min_count=min_count,
                                                  availability_zone="compute:openstack-aio")

        instances = []
        # Todo: As of now nova does not returns all the instances which it launched. It is returning only first
        # Todo: Refer openstack blueprint
        if min_count > 1:
            for endpoint_index in range(1, min_count+1):
                instance_name = "%s-%d" % (first_instance.name.rsplit('-', 1)[0], endpoint_index)
                instance = self.nova.servers.find(name=instance_name)
                while instance.status == 'BUILD':
                    time.sleep(5)
                    instance = self.nova.servers.get(instance.id)
                # Assigning floating IP to the instance
                if self.assign_floating_ip(instance):
                    instances.append(instance)

        return instances






