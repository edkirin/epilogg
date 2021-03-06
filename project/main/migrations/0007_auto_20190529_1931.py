# Generated by Django 2.2.1 on 2019-05-29 19:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_clientapp_delete_older_than'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clientapp',
            options={'ordering': ['facility__name', 'name']},
        ),
        migrations.AddField(
            model_name='logentry',
            name='type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Request'), (2, 'Response')], default=0),
        ),
        migrations.AlterField(
            model_name='clientapp',
            name='delete_older_than',
            field=models.IntegerField(blank=True, default=None, help_text='days', null=True),
        ),
    ]
