# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-07-19 21:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0004_auto_20170718_1134'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tool',
            name='configuration',
            field=models.TextField(blank=True, max_length=10000, null=True),
        ),
    ]
