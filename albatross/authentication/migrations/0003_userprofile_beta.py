# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-24 16:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_auto_20170908_1349'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='beta',
            field=models.BooleanField(default=True),
        ),
    ]