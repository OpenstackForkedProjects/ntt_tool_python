from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.db import models


class Cloud(models.Model):
    name = models.CharField(max_length=256)
    keystone_auth_url = models.CharField(max_length=2083)
    keystone_user = models.CharField(max_length=100)
    keystone_password = models.CharField(max_length=250)
    keystone_tenant_name = models.CharField(max_length=100)
    creator = models.ForeignKey(User, blank=True, null=True)
    created_on = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "clouds"


class Traffic(models.Model):
    TYPE_CHOICES = (
        ('all', 'All'),
        ('intra-tenant', 'Intra Tenant'),
        ('inter-tenant', 'Inter Tenant'),
        ('south-north', 'South to North'),
        ('north-south', 'North to South'),
    )
    TEST_ENVIRONMENT_CHOICES = (
        ('dev', 'Development/Test'),
        ('prod', 'Production'),
    )
    cloud = models.ForeignKey(Cloud, blank=True, null=True, related_name="traffics")
    name = models.CharField(max_length=256)
    allowed_delta_percentage = models.FloatField()
    test_result_path = models.CharField(max_length=250)
    number_of_workers = models.IntegerField()
    remote_user = models.CharField(max_length=100)
    remote_pass = models.CharField(max_length=100)
    test_method = models.CharField(max_length=100)
    udp_datagram_size = models.IntegerField(default=1)
    iperf_duration = models.IntegerField()
    test_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='all')
    external_host = models.CharField(max_length=100, blank=True, null=True)
    ssh_gateway = models.CharField(max_length=100, blank=True, null=True)
    test_environment = models.CharField(max_length=20, choices=TEST_ENVIRONMENT_CHOICES, default='dev')
    creator = models.ForeignKey(User, blank=True, null=True)
    created_on = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s | %s | cloud:%s" % (self.id, self.name, self.cloud.name)

    class Meta:
        db_table = "traffics"


class Tenant(models.Model):
    traffic = models.ForeignKey(Traffic, blank=True, null=True, related_name="tenants")
    tenant_id = models.CharField(max_length=100)
    tenant_name = models.CharField(max_length=256)
    description = models.CharField(max_length=256, blank=True, null=True)
    enabled = models.BooleanField(default=False)
    is_selected = models.BooleanField(default=False)
    is_dirty = models.BooleanField(default=False)
    creator = models.ForeignKey(User, blank=True, null=True)
    created_on = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s | %s | traffic:%s" % (self.id, self.tenant_name, self.traffic.name)

    class Meta:
        db_table = "tenants"


class Network(models.Model):
    tenant = models.ForeignKey(Tenant, related_name="networks")
    network_id = models.CharField(max_length=255)
    network_name = models.CharField(max_length=255)
    shared = models.BooleanField(default=False)
    status = models.CharField(max_length=25)
    is_selected = models.BooleanField(default=False)
    endpoint_count = models.IntegerField(default=True, null=True)
    is_dirty = models.BooleanField(default=False)
    creator = models.ForeignKey(User, blank=True, null=True)
    created_on = models.DateTimeField(auto_now=True)
    updated_on = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s | %s | tenant:%s" % (self.id, self.network_name, self.tenant.tenant_name)

    class Meta:
        db_table = "networks"


class Subnet(models.Model):
    network = models.ForeignKey(Network, related_name="subnets")
    subnet_id = models.CharField(max_length=255)
    subnet_name = models.CharField(max_length=255)
    cidr = models.CharField(max_length=255)
    allocation_pool_start = models.GenericIPAddressField(blank=True, null=True)
    ip_range_start = models.TextField(max_length=15, blank=True, null=True)
    ip_range_end = models.TextField(max_length=15, blank=True, null=True)
    allocation_pool_end = models.GenericIPAddressField(blank=True, null=True)
    is_dirty = models.BooleanField(default=False)

    class Meta:
        db_table = "subnets"


class Endpoint(models.Model):
    traffic = models.ForeignKey(Traffic)
    network = models.ForeignKey(Network)
    endpoint_id = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=30)
    status = models.CharField(max_length=30)
    is_selected = models.BooleanField(default=False)
    is_dirty = models.BooleanField(default=False)

    class Meta:
        db_table = "endpoints"


class TestRun(models.Model):
    TRAFFIC_TEST_RUN_STATUS = (
        ('queued', 'Queued'),
        ('inprogress', 'In Progress'),
        ('completed', 'Completed'),
        ('stopped', 'Stopped'),
        ('error', 'Error'),
    )
    traffic = models.ForeignKey(Traffic)
    report_name = models.CharField(max_length=100, blank=True, null=True)
    test_run_duration = models.IntegerField(default=1)
    started_on = models.DateTimeField(auto_now=True)
    completed_on = models.DateTimeField(auto_now=True)
    started_by = models.ForeignKey(User)
    status = models.CharField(max_length=20, choices=TRAFFIC_TEST_RUN_STATUS, default='queued')

    def __unicode__(self):
        return "%s | %s" % (self.id, self.traffic.name)

    class Meta:
        db_table = "traffic_test_run"


class UDPTestResults(models.Model):
    traffic_test_run = models.ForeignKey(TestRun, related_name="udp_test_results")
    src_tenant = models.CharField(max_length=500)
    dest_tenant = models.CharField(max_length=500)
    src_ep = models.TextField()
    dest_ep = models.TextField()
    status = models.CharField(max_length=20)
    jitter = models.CharField(max_length=20)
    bandwidth = models.CharField(max_length=20)
    bandwidth_loss_percent = models.CharField(max_length=20)
    interval_time = models.CharField(max_length=20)
    transferred = models.CharField(max_length=20)
    loss_datagram = models.CharField(max_length=20)
    total_datagram = models.CharField(max_length=20)

    def __unicode__(self):
        return "%s | TestRun: %s" % (self.id, self.traffic_test_run.id)

    class Meta:
        db_table = "udp_test_results"


class ICMPTestResults(models.Model):
    traffic_test_run = models.ForeignKey(TestRun, related_name="icmp_test_results")
    src_tenant = models.CharField(max_length=500)
    dest_tenant = models.CharField(max_length=500)
    src_ep = models.TextField()
    dest_ep = models.TextField()
    status = models.CharField(max_length=20)
    rtt_min = models.FloatField()
    rtt_max = models.FloatField()
    rtt_avg = models.FloatField()
    packets_received = models.IntegerField()
    packets_transmitted = models.IntegerField()
    packet_loss_percent = models.FloatField()

    def __unicode__(self):
        return "%s | TestRun: %s" % (self.id, self.traffic_test_run.id)

    class Meta:
        db_table = "icmp_test_results"


class TCPTestResults(models.Model):
    traffic_test_run = models.ForeignKey(TestRun, related_name="tcp_test_results")
    src_tenant = models.CharField(max_length=500)
    dest_tenant = models.CharField(max_length=500)
    src_ep = models.TextField()
    dest_ep = models.TextField()
    status = models.CharField(max_length=20)
    retr = models.IntegerField()
    bandwidth = models.CharField(max_length=20)
    interval_time = models.CharField(max_length=20)
    transferred = models.CharField(max_length=20)

    def __unicode__(self):
        return "%s | TestRun: %s" % (self.id, self.traffic_test_run.id)

    class Meta:
        db_table = "tcp_test_results"
