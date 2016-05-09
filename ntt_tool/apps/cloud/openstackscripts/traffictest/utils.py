def get_default_icmp_contract():
    contract = {
         'name': 'allow_icmp',
         'protocol': 'icmp',
         'port': 'None',
         'direction': 'in',
         'action': 'allow'
    }
    return contract


def get_default_tcp_contract():
    contract = {
        'name': 'allow_ssh',
        'protocol': 'tcp',
        'port': '22',
        'direction': 'in',
        'action': 'allow'
    }
    return contract


def get_default_udp_contract():
    contract = {
        'name': 'allow_udp',
        'protocol': 'udp',
        'port': 'None',
        'direction': 'in',
        'action': 'allow'
    }
    return contract


def test_method_contracts(test_method):
    function_dict = {
        "icmp": get_default_icmp_contract,
        "tcp": get_default_tcp_contract,
        "udp": get_default_udp_contract
    }
    return function_dict[test_method]()



