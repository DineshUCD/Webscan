# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-28 21:52
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scan',
            name='application_id',
        ),
    ]
