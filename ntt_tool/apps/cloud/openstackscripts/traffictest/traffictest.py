import time
from ntt_tool.apps.cloud.models import *
from ntt_tool.apps.cloud.serializers import TestRunSerializer
from utils import *
from ntt_tool.apps.cloud.openstackscripts.traffictest.libs import traf_tester


class TrafficTest(object):

    def __init__(self, traffic_id):
        self.traffic = Traffic.objects.get(pk=traffic_id)

    def run_test(self, started_by, duration=1):
        test_run = TestRun()
        test_run.traffic = self.traffic
        test_run.test_run_duration = duration
        test_run.started_by = started_by
        test_run.save()



        try:
            endpoints_list = self.generate_endpoints_contract_list()
            setup_config = self.generate_setup_config()
            traf_tester.start_task(setup_config, endpoints_list, "start", "_".join(self.traffic.name.split()))
            time.sleep(60 * duration)
            test_results = traf_tester.start_task(setup_config, endpoints_list, "stop", "_".join(self.traffic.name.split()))

            for test_method, results in test_results.iteritems():
                if test_method == "udp":
                    for udp_test_result in results:
                        udp_res_obj = UDPTestResults()
                        udp_res_obj.traffic_test_run = test_run
                        udp_res_obj.src_tenant = udp_test_result.get('src_tenant')[0]
                        udp_res_obj.dest_tenant = udp_test_result.get('dest_tenant')[0]
                        udp_res_obj.src_ep = udp_test_result.get('src_ep')
                        udp_res_obj.dest_ep = udp_test_result.get('dest_ep')
                        udp_res_obj.status = udp_test_result.get('status')
                        udp_res_obj.jitter = udp_test_result.get('jitter')
                        udp_res_obj.bandwidth = udp_test_result.get('bandwidth')
                        udp_res_obj.bandwidth_loss_percent = udp_test_result.get('bandwidth_loss_percent')
                        udp_res_obj.interval_time = udp_test_result.get('interval_time')
                        udp_res_obj.transferred = udp_test_result.get('transferred')
                        udp_res_obj.loss_datagram = udp_test_result.get('loss_datagram')
                        udp_res_obj.total_datagram = udp_test_result.get('total_datagram')
                        udp_res_obj.save()
                elif test_method == "icmp":
                    for icmp_test_result in results:
                        icmp_res_obj = ICMPTestResults()
                        icmp_res_obj.traffic_test_run = test_run
                        icmp_res_obj.src_tenant = icmp_test_result.get('src_tenant')[0]
                        icmp_res_obj.dest_tenant = icmp_test_result.get('dest_tenant')[0]
                        icmp_res_obj.src_ep = icmp_test_result.get('src_ep')
                        icmp_res_obj.dest_ep = icmp_test_result.get('dest_ep')
                        icmp_res_obj.status = icmp_test_result.get('status')
                        icmp_res_obj.rtt_min = icmp_test_result.get('rtt_min')
                        icmp_res_obj.rtt_max = icmp_test_result.get('rtt_max')
                        icmp_res_obj.rtt_avg = icmp_test_result.get('rtt_avg')
                        icmp_res_obj.packets_received = icmp_test_result.get('packets_received')
                        icmp_res_obj.packets_transmitted = icmp_test_result.get('packets_transmitted')
                        icmp_res_obj.packet_loss_percent = icmp_test_result.get('packet_loss_percent')
                        icmp_res_obj.save()
                elif test_method == "tcp":
                    for tcp_test_result in results:
                        tcp_res_obj = TCPTestResults()
                        tcp_res_obj.traffic_test_run = test_run
                        tcp_res_obj.src_tenant = tcp_test_result.get('src_tenant')[0]
                        tcp_res_obj.dest_tenant = tcp_test_result.get('dest_tenant')[0]
                        tcp_res_obj.src_ep = tcp_test_result.get('src_ep')
                        tcp_res_obj.dest_ep = tcp_test_result.get('dest_ep')
                        tcp_res_obj.retr = tcp_test_result.get('retr')
                        tcp_res_obj.bandwidth = tcp_test_result.get('bandwidth')
                        tcp_res_obj.interval_time = tcp_test_result.get('interval_time')
                        tcp_res_obj.transferred = tcp_test_result.get('transferred')
                        tcp_res_obj.save()
        except Exception, e:
            test_run.status = "error"
            test_run.save()
            raise e
        test_run.status = "completed"
        test_run.save()

        serializer = TestRunSerializer(test_run)
        return serializer.data

    def stop_test(self):
        pass

    def generate_endpoints_contract_list(self):
        endpoint_contract_configs = []
        if self.traffic.test_type == 'intra-tenant':
            subnet_endpoints_map = {}
            endpoints = Endpoint.objects.filter(traffic_id=self.traffic.id).filter(is_selected=True)
            for endpoint in endpoints:
                subnet = endpoint.network.subnets.first()
                if subnet.subnet_name not in subnet_endpoints_map:
                    subnet_endpoints_map[subnet.subnet_name] = {
                        'endpoints': [],
                        'id': subnet.subnet_id,
                        'name': subnet.subnet_name
                    }
                subnet_endpoints_map[subnet.subnet_name]['endpoints'].append(endpoint.ip_address)

            net = {}
            for entry in subnet_endpoints_map.values():
                tsrc = []
                tdest = []
                tsrc.append(entry['endpoints'])
                for nextep in subnet_endpoints_map.values():
                    if entry['name'] != nextep['name']:
                        tdest.append(nextep['endpoints'])
                        subnet_data = {
                            'src_eps': [ep for eps in tsrc for ep in eps],
                            'dest_eps': [ep for eps in tdest for ep in eps]
                        }
                        net[entry['name']] = subnet_data

            tenants = [x.tenant_name for x in self.traffic.tenants.filter(is_selected=True)]
            for k, src_dst_eps in net.iteritems():
                config = {
                    'contract': [],
                    'test_type': self.traffic.test_type,
                    'src_tenant': tenants,
                    'dest_eps': src_dst_eps.get('dest_eps'),
                    'src_eps': src_dst_eps.get('src_eps')
                }
                for test_method in self.traffic.test_method.split(','):
                    config.get('contract').append(test_method_contracts(test_method))
                config['dest_tenant'] = tenants
                endpoint_contract_configs.append(config)
        return endpoint_contract_configs

    def generate_setup_config(self):
        setup_config = {}
        cloud = self.traffic.cloud
        setup_config['default'] = {
            'keystone_auth_url': cloud.keystone_auth_url,
            'keystone_user': cloud.keystone_user,
            'keystone_password': cloud.keystone_password,
            'keystone_tenant_name': cloud.keystone_tenant_name
        }
        setup_config['traffic'] = {
            'allowed_delta_percentage': self.traffic.allowed_delta_percentage,
            'test_results_path': self.traffic.test_result_path,
            'number_of_workers': self.traffic.number_of_workers,
            'remote_user': self.traffic.remote_user,
            'remote_pass': self.traffic.remote_pass,
            'test_method': self.traffic.test_method.split(','),
            'iperf_duration': self.traffic.iperf_duration,
            'type': self.traffic.test_type
        }
        setup_config['tenants'] = {'tenants': []}
        setup_config['tenant_ssh_gateway'] = {}
        for tenant in self.traffic.tenants.all():
            setup_config['tenants']['tenants'].append(tenant.tenant_name)
            setup_config['tenant_ssh_gateway'][tenant.tenant_name] = self.traffic.ssh_gateway
        setup_config['external_host'] = {'host': self.traffic.external_host}
        return setup_config
