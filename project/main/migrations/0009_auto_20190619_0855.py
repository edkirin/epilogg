# Generated by Django 2.2.1 on 2019-06-19 08:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0008_auto_20190529_1950'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clientapp',
            name='api_key',
        ),
        migrations.AddField(
            model_name='logentry',
            name='group',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='logentry',
            name='user',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logentry_user', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='logentry',
            name='category',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='logentry',
            name='format',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Plain'), (1, 'Json'), (2, 'XML'), (3, 'YAML')], default=0),
        ),
    ]
