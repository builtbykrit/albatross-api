# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-31 13:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0002_auto_20170831_1331'),
        ('projects', '0006_auto_20170829_2059'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='team',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='projects', to='teams.Team'),
        ),
    ]