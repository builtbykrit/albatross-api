# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-11-02 19:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0006_auto_20171013_2035'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='wants_weekly_emails',
            field=models.BooleanField(default=True),
        ),
    ]