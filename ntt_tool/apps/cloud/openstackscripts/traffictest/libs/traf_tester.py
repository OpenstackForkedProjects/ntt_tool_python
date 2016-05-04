import json
import logging
import os
import re
import time
import fabtools

from itertools import *
from operator import *
from fabric.api import *


traffic_test_script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts')
test_results_path = '~/dp_test_results'

logger = logging.getLogger(__name__)


def unique_justseen(iterable, key=None):
    "List unique elements, preserving order. Remember only the element just seen."
    return imap(next, imap(itemgetter(1), groupby(iterable, key)))


def setup_env(config, endpoints):
    env.hosts = endpoints.get("src_eps")
    env.user = config.get('traffic', {}).get('remote_user')
    env.password = config.get('traffic', {}).get('remote_pass')
    env.skip_bad_hosts = True
    if endpoints['test_type'] != 'north-south':
        env.gateway = config.get('tenant_ssh_gateway', {}).get(endpoints.get('src_tenant')[0])
    else:
        env.gateway = config.get('tenant_ssh_gateway', {}).get(endpoints.get('dest_tenant')[0])


def install_hping(environment):
    try:
        out = run("python -c 'import platform;"
                  " print platform.linux_distribution()[0]'")
        os_info = out
        logger.debug("Host %s runs %s" % (env.host_string, os_info))
        if out.return_code == 0:
            if os_info in ['CentOS',
                           'Red Hat Enterprise Linux Server',
                           'Fedora']:
                out = sudo("yum -y install hping3")
                if out.return_code == 0:
                    logger.info("Installed hping3 on %s" % (env.host_string))
            elif os_info in ['Ubuntu','LinuxMint']:
                out = sudo("apt-get -y install hping3")
                if out.return_code == 0:
                    logger.info("Installed hping3 on %s" % (env.host_string))
        out = run("mkdir %s" % (test_results_path))
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


def install_iperf(environment):
    try:
        # out = run("python -c 'import platform;"
        #           " print platform.linux_distribution()[0]'")
        # os_info = out

        os_distribution_id = fabtools.system.distrib_id()
        logger.debug("Host %s runs %s" % (env.host_string, os_distribution_id))
        # if out.return_code == 0:
        if os_distribution_id in ['CentOS','Red Hat Enterprise Linux Server', 'Fedora']:
            out = sudo("yum -y install iperf3")
            if out.return_code == 0:
                logger.info("Installed iperf3 on %s" % (env.host_string))
        elif os_distribution_id in ['Ubuntu','LinuxMint']:
            if not fabtools.deb.is_installed("iperf3"):
                fabtools.deb.update_index()
                fabtools.deb.install("iperf3")
                # run("sudo apt-get update -y")
                # out = sudo("apt-get -y install iperf3")
                # if out.return_code == 0:
                #     logger.info("Installed iperf3 on %s" % (env.host_string))
        run("mkdir %s" % (test_results_path))
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


def setup_iperf_env(config, src_tenant, dest_tenant, endpoints, test_type):
    env.hosts = endpoints
    env.user = config.get('traffic', {}).get('remote_user')
    env.password = config.get('traffic', {}).get('remote_pass')
    env.skip_bad_hosts = True
    if test_type != 'north-south':
        env.gateway = config.get('tenant_ssh_gateway', {}).get(src_tenant[0])
    else:
        env.gateway = config.get('tenant_ssh_gateway', {}).get(dest_tenant[0])


@task
@parallel
def create_test_results_directory(environment):
    try:
        run("mkdir %s" % (test_results_path))
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


@task
@parallel
def test_ping(environment, config, endpoints, contract, timestamp):
    try:
        for dest_ep in endpoints['dest_eps']:
            if dest_ep != env.host_string:
                #sudo("hping3 %s --icmp --fast -q 2>"
                #     " testtraffic-%s-%s-%s.txt 1> /dev/null &" %
                sudo("hping3 %s --icmp --fast -q >"
                     " testtraffic-%s-%s-%s.txt 2>&1 &" %
                     (dest_ep,
                      env.host_string.replace('.', '_'),
                      dest_ep.replace('.', '_'),
                      timestamp),
                     pty=False)

    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


@task
@parallel
def test_tcp(environment, config, server, endpoints, contract, timestamp):
    try:
        if server == '':
            print "TCP server execution"
            for src_ep in endpoints:
                if src_ep == env.host_string:
                    print src_ep

                    sudo("iperf3 -s -p 5201 -i 1 > tcptesttrafficserver-%s-%s.txt 2>&1 &" %
                         (env.host_string.replace('.', '_'),
                          timestamp),
                         pty=False)

        else:
            print "TCP client execution"
            for dest_ep in endpoints:
                if dest_ep == env.host_string:
                    print dest_ep

                    sudo("iperf3 -c %s -t %s -p 5201 > tcptesttrafficclient-%s-%s-%s.txt 2>&1 &" %
                         (server,
                          config['traffic']['iperf_duration'],
                          env.host_string.replace('.', '_'),
                          server.replace('.', '_'),
                          timestamp),
                         pty=False)

    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


@task
@parallel
def test_udp(environment, config, server, endpoints, contract, timestamp):
    try:
        if server == '':
            print "UDP server execution"
            for src_ep in endpoints:
                if src_ep == env.host_string:
                    print src_ep

                    sudo("iperf3 -s -p 5202 -i 1 > udptesttrafficserver-%s-%s.txt 2>&1 &" %
                         (env.host_string.replace('.', '_'),
                          timestamp),
                         pty=False)

        else:
            print "UDP client execution"
            for dest_ep in endpoints:
                if dest_ep == env.host_string:
                    print dest_ep

                    sudo("iperf3 -c %s -u -n %sm -b 10m -p 5202 > udptesttrafficclient-%s-%s-%s.txt 2>&1 &" %
                         (server,
                          config.get("traffic", {}).get("udp_datagram_size", 1),
                          env.host_string.replace('.', '_'),
                          server.replace('.', '_'),
                          timestamp),
                         pty=False)

    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


def capture_output():
    pass


@task
@parallel
def stop_traffic(environment, endpoints, timestamp):
    try:
        try:
            sudo("kill -SIGINT `pgrep hping3`")
        except SystemExit, e:
            logger.warn("Exception while executing task: %s", str(e))

        print "dest_eps are.....", endpoints['dest_eps']
        put(os.path.join(traffic_test_script_dir, "get_ping_statistics.py"), "get_ping_statistics.py")
        out = run("python get_ping_statistics.py %s" % (timestamp))
        out_dict = json.JSONDecoder().decode(out)
        output = {'src_tenant': endpoints['src_tenant'], 'dest_tenant': endpoints['dest_tenant'], 'test_result': out_dict}
        return output
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))



@task
@parallel
def stop_iperf_traffic(environment, traffic_type, server, dest_ep, src_tenant, dest_tenant, timestamp):
    try:

        if server == '':
            try:
                print "Killing iperf on server"
                sudo("kill -SIGINT `pgrep iperf`")
            except SystemExit, e:
                logger.warn("Exception while executing task: %s", str(e))

            print "server endpoint is.....", dest_ep

            return True
        else:

            try:
                print "Killing iperf on client"
                sudo("kill -SIGINT `pgrep iperf`")
            except SystemExit, e:
                logger.warn("Exception while executing task: %s", str(e))

            print "client endpoint is.....", dest_ep

            if traffic_type == 'tcp':
                put(os.path.join(traffic_test_script_dir, "get_iperf_tcp_statistics.py"), "get_iperf_tcp_statistics.py")
                out = run("python get_iperf_tcp_statistics.py %s-%s-%s" %
                          (dest_ep.replace('.', '_'),
                           server.replace('.', '_'),
                           timestamp))

            if traffic_type == 'udp':
                put(os.path.join(traffic_test_script_dir, "get_iperf_udp_statistics.py"), "get_iperf_udp_statistics.py")
                out = run("python get_iperf_udp_statistics.py %s-%s-%s" %
                          (dest_ep.replace('.', '_'),
                           server.replace('.', '_'),
                           timestamp))

            out_dict = json.JSONDecoder().decode(out)
            return {'src_tenant': src_tenant, 'dest_tenant': dest_tenant, 'test_result': out_dict}
    except SystemExit, e:
        logger.warn("Exception while executing task: %s", str(e))


def format_icmp_test_results(data, allowed_delta_percentage):
    status = None
    test_results = []
    dest_ep_regex = ".*-*-(?P<dest_ip>[0-9]+_[0-9]+_[0-9]+_[0-9]+)-.*"
    for content in data:
        for k, v in content.items():
            src_ep = k
            src_tenant = v['src_tenant']
            dest_tenant = v['dest_tenant']
            test_result_files = v['test_result'].keys()
            for test_result_file in test_result_files:
                dest_ep_match = re.match(dest_ep_regex, test_result_file)
                dest_ep = dest_ep_match.group('dest_ip')
                packet_stats = v['test_result'][test_result_file]['packet_stats']
                packet_loss_percent = packet_stats['packet_loss']  # NOQA
                try:
                    if packet_loss_percent <= int(allowed_delta_percentage):  # NOQA
                        status = 'Success'
                    else:
                        status = 'Failed'
                except ValueError:
                    status = 'Failed'
                rtt_stats = v['test_result'][test_result_file]['rtt']
                test_results.append({
                    "src_tenant": src_tenant,
                    "src_ep": src_ep,
                    "dest_tenant": dest_tenant,
                    "dest_ep": dest_ep.replace('_', '.'),
                    "packets_transmitted": packet_stats['packets_transmitted'],
                    "packets_received": packet_stats['packets_received'],
                    "packet_loss_percent": packet_loss_percent,
                    "rtt_min": rtt_stats['rtt_min'],
                    "rtt_avg": rtt_stats['rtt_avg'],
                    "rtt_max": rtt_stats['rtt_max'],
                    "status": status,
                })
    return test_results


def format_tcp_test_results(data):
    test_results = []
    status = None
    dest_ep_regex = ".*-*-(?P<dest_ip>[0-9]+_[0-9]+_[0-9]+_[0-9]+)-.*"
    for content in data:
        for k, v in content.items():
            src_ep = k
            src_tenant = v['src_tenant']
            dest_tenant = v['dest_tenant']
            test_result_files = v['test_result'].keys()
            for test_result_file in test_result_files:
                dest_ep_match = re.match(dest_ep_regex, test_result_file)
                dest_ep = dest_ep_match.group('dest_ip')
                bandwidth_stats = v['test_result'][test_result_file]['bandwidth_stats']
                if bandwidth_stats['interval_time'] and bandwidth_stats['transferred'] and bandwidth_stats['bandwidth']:
                    status = "Success"
                else:
                    status = "Failed"
                test_results.append({
                    "src_tenant": src_tenant,
                    "src_ep": src_ep,
                    "dest_tenant": dest_tenant,
                    "dest_ep": dest_ep.replace('_', '.'),
                    "interval_time": bandwidth_stats['interval_time'],
                    "transferred": bandwidth_stats['transferred'],
                    "bandwidth": bandwidth_stats['bandwidth'],
                    "retr": bandwidth_stats['retr'],
                    "status": status
                })
    return test_results


def format_udp_test_results(data):
    test_results = []
    status = None
    dest_ep_regex = ".*-*-(?P<dest_ip>[0-9]+_[0-9]+_[0-9]+_[0-9]+)-.*"
    for content in data:
        for k, v in content.items():
            src_ep = k
            src_tenant = v['src_tenant']
            dest_tenant = v['dest_tenant']
            test_result_files = v['test_result'].keys()
            for test_result_file in test_result_files:
                dest_ep_match = re.match(dest_ep_regex, test_result_file)
                dest_ep = dest_ep_match.group('dest_ip')
                bandwidth_stats = v['test_result'][test_result_file]['bandwidth_stats']
                if bandwidth_stats['loss_percent'] != '':
                    bandwidth_loss_percent = \
                    bandwidth_stats['loss_percent']+" %"  # NOQA
                else:
                    bandwidth_loss_percent = ""
                if bandwidth_stats['interval_time'] and bandwidth_stats['transferred'] and bandwidth_stats['bandwidth']:
                    status = "Success"
                else:
                    status = "Failed"
                test_results.append({
                    "src_tenant": src_tenant,
                    "src_ep": src_ep,
                    "dest_tenant": dest_tenant,
                    "dest_ep": dest_ep.replace('_', '.'),
                    "interval_time": bandwidth_stats['interval_time'],
                    "transferred": bandwidth_stats['transferred'],
                    "bandwidth": bandwidth_stats['bandwidth'],
                    "jitter": bandwidth_stats['jitter'],
                    "loss_datagram": bandwidth_stats['loss_datagram'],
                    "total_datagram": bandwidth_stats['total_datagram'],
                    "bandwidth_loss_percent": bandwidth_loss_percent,
                    "status": status
                })
    return test_results


def start_task(config, endpoints_list, action, testPrefix=None):
    timestamp = testPrefix
    if not testPrefix:
        timestamp = time.strftime("%Y-%m-%d-%H-%M-%S")

    output_table_data_list = []
    tcp_output_table_data_list = []
    udp_output_table_data_list = []
    table_data = {}
    iperf_endpoint_list = list(unique_justseen(endpoints_list, key=itemgetter('test_type')))
    if action == 'start':
        for endpoints in endpoints_list:
            for contract in endpoints['contract']:
                if contract['protocol'] == 'icmp':
                    setup_env(config, endpoints)
                    execute(create_test_results_directory, env)
                    execute(install_hping, env)
                    execute(test_ping, env, config, endpoints, contract, timestamp)
        for fullendpoints in iperf_endpoint_list:
            endpoints = {}
            endpoints['contract'] = fullendpoints['contract']
            endpoints['src_tenant'] = fullendpoints['src_tenant']
            endpoints['src_eps'] = [fullendpoints['src_eps'][0]]
            endpoints['dest_tenant'] = fullendpoints['dest_tenant']
            endpoints['dest_eps'] = [fullendpoints['dest_eps'][0]]
            endpoints['test_type'] = fullendpoints['test_type']
            for contract in endpoints['contract']:
                if contract['protocol'] == 'tcp':
                    server_ip = [endpoints['dest_eps'][0]]
                    client_ip = endpoints['src_eps']
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], server_ip, endpoints['test_type'])
                    execute(create_test_results_directory, env)
                    execute(install_iperf, env)
                    server = ''
                    execute(test_tcp, env, config, server, server_ip, contract, timestamp)
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], client_ip, endpoints['test_type'])
                    execute(install_iperf, env)
                    server = server_ip[0]
                    execute(test_tcp, env, config, server, client_ip, contract, timestamp)
                if contract['protocol'] == 'udp':
                    server_ip = [endpoints['dest_eps'][0]]
                    client_ip = endpoints['src_eps']
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], server_ip, endpoints['test_type'])
                    execute(create_test_results_directory, env)
                    execute(install_iperf, env)
                    server = ''
                    execute(test_udp, env, config, server, server_ip, contract, timestamp)
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], client_ip, endpoints['test_type'])
                    execute(install_iperf, env)
                    server = server_ip[0]
                    execute(test_udp, env, config, server, client_ip, contract, timestamp)
    
    if action == 'stop':
        for endpoints in endpoints_list:
            for contract in endpoints['contract']:
                if contract['protocol'] == 'icmp':
                    setup_env(config, endpoints)
                    table_data = execute(stop_traffic, env, endpoints, timestamp)
                    output_table_data_list.append(table_data)
        for fullendpoints in iperf_endpoint_list:
            endpoints = {}
            endpoints['contract'] = fullendpoints['contract']
            endpoints['src_tenant'] = fullendpoints['src_tenant']
            endpoints['src_eps'] = [fullendpoints['src_eps'][0]]
            endpoints['dest_tenant'] = fullendpoints['dest_tenant']
            endpoints['dest_eps'] = [fullendpoints['dest_eps'][0]]
            endpoints['test_type'] = fullendpoints['test_type']
            for contract in endpoints['contract']:
                if contract['protocol'] == 'tcp':
                    server_ip = [endpoints['dest_eps'][0]]
                    client_ip = endpoints['src_eps']
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], server_ip, endpoints['test_type'])
                    server = ''
                    execute(stop_iperf_traffic, env, 'tcp', server, server_ip[0], endpoints['src_tenant'], endpoints['dest_tenant'], timestamp)
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], client_ip, endpoints['test_type'])
                    server = server_ip[0]
                    for dest_ep in client_ip:
                        table_data = execute(stop_iperf_traffic, env, 'tcp', server, dest_ep, endpoints['src_tenant'], endpoints['dest_tenant'], timestamp)
                        tcp_output_table_data_list.append(table_data)
                if contract['protocol'] == 'udp':
                    server_ip = [endpoints['dest_eps'][0]]
                    client_ip = endpoints['src_eps']
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], server_ip, endpoints['test_type'])
                    server = ''
                    execute(stop_iperf_traffic, env, 'udp', server, server_ip[0], endpoints['src_tenant'], endpoints['dest_tenant'], timestamp)
                    setup_iperf_env(config, endpoints['src_tenant'], endpoints['dest_tenant'], client_ip, endpoints['test_type'])
                    server = server_ip[0]
                    for dest_ep in client_ip:
                        table_data = execute(stop_iperf_traffic, env, 'udp', server, dest_ep, endpoints['src_tenant'], endpoints['dest_tenant'], timestamp)
                        udp_output_table_data_list.append(table_data)

    traffic_test_result = {
        "icmp": format_icmp_test_results(output_table_data_list, config.get('traffic', {}).get('allowed_delta_percentage')),
        "tcp": format_tcp_test_results(tcp_output_table_data_list),
        "udp": format_udp_test_results(udp_output_table_data_list,)
    }
    return traffic_test_result

