# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-28 19:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('plans', '0001_initial'),
        ('accounts', '0002_auto_20170328_1251'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetaFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report', models.FilePathField(default='', match='.*\\.(log|json|ini|xml|yml|zip|w3af|afr)')),
                ('role', models.CharField(choices=[('D', 'Documentation'), ('S', 'Scan')], default='D', max_length=1)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Scan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uniform_resource_locator', models.URLField(help_text='Please use the following format: http(s)://', max_length=2083)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(choices=[('PENDING', 'Pending'), ('STARTED', 'Started'), ('SUCCESS', 'Success'), ('FAILURE', 'Failure')], default='PENDING', max_length=7)),
                ('task_id', models.UUIDField(default=uuid.uuid4)),
            ],
        ),
        migrations.CreateModel(
            name='Tool',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('module', models.CharField(blank=True, default='', max_length=256)),
                ('name', models.CharField(blank=True, default='', max_length=256)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('state', models.CharField(blank=True, choices=[('PENDING', 'Pending'), ('STARTED', 'Started'), ('SUCCESS', 'Success'), ('FAILURE', 'Failure')], max_length=7)),
                ('task_id', models.UUIDField(blank=True, default=uuid.uuid4)),
            ],
        ),
        migrations.CreateModel(
            name='PassFailTool',
            fields=[
                ('tool_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='scans.Tool')),
                ('test', models.NullBooleanField()),
            ],
            bases=('scans.tool',),
        ),
        migrations.CreateModel(
            name='Zip',
            fields=[
                ('scan', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='scans.Scan')),
                ('name', models.CharField(default='', max_length=256)),
                ('uploaded_to', models.FilePathField(default='')),
                ('date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='tool',
            name='plan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='plans.Plan'),
        ),
        migrations.AddField(
            model_name='scan',
            name='user_profile',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.UserProfile'),
        ),
        migrations.AddField(
            model_name='metafile',
            name='scan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scans.Scan'),
        ),
        migrations.AddField(
            model_name='metafile',
            name='tool',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='scans.Tool'),
        ),
        migrations.AlterUniqueTogether(
            name='scan',
            unique_together=set([('user_profile', 'id')]),
        ),
        migrations.AddField(
            model_name='metafile',
            name='store',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scans.Zip'),
        ),
    ]
