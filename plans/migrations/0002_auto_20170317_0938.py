# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-17 16:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('plans', '0001_initial'),
        ('scans', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='scan',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scans.Scan'),
        ),
        migrations.AddField(
            model_name='plan',
            name='user_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.UserProfile'),
        ),
    ]
