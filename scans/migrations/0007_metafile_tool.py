# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-11-16 23:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scans', '0006_auto_20161031_1908'),
    ]

    operations = [
        migrations.AddField(
            model_name='metafile',
            name='tool',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
    ]