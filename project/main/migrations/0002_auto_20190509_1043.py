# Generated by Django 2.2.1 on 2019-05-09 10:43

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientapp',
            name='api_key',
            field=models.UUIDField(db_index=True, default=uuid.uuid4),
        ),
        migrations.AlterField(
            model_name='clientapp',
            name='id',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, primary_key=True, serialize=False),
        ),
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('level', models.PositiveSmallIntegerField(choices=[(0, 'Not set'), (10, 'Debug'), (20, 'Info'), (30, 'Warning'), (40, 'Error'), (50, 'Critical')], default=0)),
                ('format', models.PositiveSmallIntegerField(choices=[(0, 'Plain'), (1, 'Json')], default=0)),
                ('data', models.TextField(blank=True, default=None, null=True)),
                ('vars', models.TextField(blank=True, default=None, null=True)),
                ('confirmed', models.BooleanField(default=False)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('client_app', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.ClientApp')),
            ],
            options={
                'db_table': 'log_entries',
                'ordering': ['-timestamp'],
            },
        ),
    ]