# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-03 19:47
from __future__ import unicode_literals

import django
from django.db import migrations, models
import picklefield

class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0011_auto_20170908_1722'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='last_weeks_hours',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='last_imported_date',
            field=models.DateTimeField(blank=True, null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='previous_weeks_hours',
            field=django.contrib.postgres.fields.ArrayField(base_field=picklefield.fields.PickledObjectField(editable=False),
                                                   blank=True, default=list, size=None),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='project',
            name='archived',
            field=models.BooleanField(default=False),
        ),

    ]