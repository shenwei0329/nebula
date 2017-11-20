# coding=utf-8
from netaddr import IPNetwork, IPAddress


def first_ip(cidr):
    network = IPNetwork(cidr)
    return IPAddress(network.first).format()


def last_ip(cidr):
    network = IPNetwork(cidr)
    return IPAddress(network.last).format()
