# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-09 12:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0013_auto_20160509_1227'),
    ]

    operations = [
        migrations.RenameField(
            model_name='udptestresults',
            old_name='cpu_utilization_desc',
            new_name='cpu_utilization_dest',
        ),
    ]
