# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-04 19:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0002_auto_20170328_1251'),
        ('scans', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='State',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(blank=True, choices=[('PENDING', 'Pending'), ('STARTED', 'Started'), ('SUCCESS', 'Success'), ('FAILURE', 'Failure')], max_length=7)),
                ('task_id', models.UUIDField(blank=True, default=uuid.uuid4)),
                ('test', models.NullBooleanField()),
            ],
        ),
        migrations.RemoveField(
            model_name='passfailtool',
            name='tool_ptr',
        ),
        migrations.RemoveField(
            model_name='scan',
            name='state',
        ),
        migrations.RemoveField(
            model_name='scan',
            name='task_id',
        ),
        migrations.RemoveField(
            model_name='tool',
            name='date',
        ),
        migrations.RemoveField(
            model_name='tool',
            name='plan',
        ),
        migrations.RemoveField(
            model_name='tool',
            name='state',
        ),
        migrations.RemoveField(
            model_name='tool',
            name='task_id',
        ),
        migrations.AddField(
            model_name='tool',
            name='plans',
            field=models.ManyToManyField(to='plans.Plan'),
        ),
        migrations.DeleteModel(
            name='PassFailTool',
        ),
        migrations.AddField(
            model_name='state',
            name='scan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scans.Scan'),
        ),
        migrations.AddField(
            model_name='state',
            name='tool',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scans.Tool'),
        ),
    ]
