# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-03 10:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cloud', '0006_auto_20160503_0958'),
    ]

    operations = [
        migrations.AlterField(
            model_name='traffic',
            name='test_method',
            field=models.CharField(default='', max_length=100),
            preserve_default=False,
        ),
    ]
