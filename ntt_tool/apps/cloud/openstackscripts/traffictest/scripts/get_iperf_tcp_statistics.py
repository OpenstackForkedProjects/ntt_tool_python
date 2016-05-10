import json
import os
import re
import sys


fileid = sys.argv[1]
filedir = os.getcwd()


def get_list_of_filenames():
    file_list = []
    for file in os.listdir(filedir):
        if file.startswith("tcptesttrafficclient") and file.endswith("%s.json" % (fileid)):
            file_list.append(file)
    return file_list


def process_files(file_list):
    out = {}
    for file in file_list:
        out[file] = get_test_results(file)
    return out


def get_test_results(file):
    """
    For a given test output file, return a tuple of the following format
    (bandwidth_loss dict wth keys interval_time, transferred, bandwidth, 
     jitter, loss_datagram, total_datagram, loss_percent)
    """

    try:
        with open(file, 'r') as f:
            out = json.loads(f.read())
            result = {}
            result['src_endpoints'] = [x.get('local_host') for x in out.get('start', {}).get('connected', [])]
            result['dest_endpoints'] = [x.get('remote_host') for x in out.get('start', {}).get('connected', [])]
            result['retransmits'] = out.get("end", {}).get("sum_sent", {}).get("retransmits", 0)
            result['bandwidth'] = out.get("end", {}).get("sum_sent", {}).get("bits_per_second", 0)
            result['interval_time_start'] = out.get("end", {}).get("sum_sent", {}).get("start", 0)
            result['interval_time_end'] = out.get("end", {}).get("sum_sent", {}).get("end", 0)
            result['bytes_transferred'] = out.get("end", {}).get("sum_sent", {}).get("bytes", 0)
            result['cpu_utilization_src'] = out.get("end", {}).get("cpu_utilization_percent", {}).get("host_total", 0)
            result['cpu_utilization_dest'] = out.get("end", {}).get("cpu_utilization_percent", {}).get("remote_total", 0)
            result['status'] = 'success'
            return result
    except IOError, e:
        raise e
    except Exception, e:
        raise e


def main():
    file_list = get_list_of_filenames()
    script_output = process_files(file_list)
    json_output = json.JSONEncoder().encode(script_output)
    # sample output
    # {'test.txt': ({'packet_loss': '0%'},
    #               {'rtt_min': '4.3', 'rtt_avg': '5.5', 'rtt_max': '6.3'})}
    print json_output

if __name__ == '__main__':
    main()
