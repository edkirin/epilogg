# Generated by Django 2.2.1 on 2019-07-29 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0010_auto_20190620_1647'),
    ]

    operations = [
        migrations.AddField(
            model_name='logentry',
            name='bulk_uuid',
            field=models.CharField(blank=True, db_index=True, max_length=40, null=True),
        ),
    ]
