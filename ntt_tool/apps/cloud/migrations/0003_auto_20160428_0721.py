# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-28 07:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0002_auto_20160427_0922'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TrafficTestRun',
            new_name='TestRun',
        ),
    ]
