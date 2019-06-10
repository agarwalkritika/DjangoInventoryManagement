# Generated by Django 2.2.1 on 2019-06-09 06:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Approvals',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=10)),
                ('product_name', models.CharField(max_length=32)),
                ('vendor', models.CharField(max_length=32)),
                ('mrp', models.FloatField()),
                ('batch_num', models.CharField(max_length=32)),
                ('batch_date', models.DateField()),
                ('quantity', models.IntegerField()),
                ('status', models.CharField(choices=[('APPROVED', 'APPROVED'), ('PENDING', 'PENDING')], max_length=8)),
                ('request_id', models.CharField(max_length=32)),
                ('operation', models.CharField(choices=[('UPDATE', 'UPDATE'), ('CREATE', 'CREATE'), ('DELETE', 'DELETE')], max_length=10)),
                ('email_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
