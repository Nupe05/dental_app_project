# Generated by Django 5.2.3 on 2025-06-21 20:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('claims', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ToothRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tooth_number', models.IntegerField(choices=[(1, 'Tooth 1'), (2, 'Tooth 2'), (3, 'Tooth 3'), (4, 'Tooth 4'), (5, 'Tooth 5'), (6, 'Tooth 6'), (7, 'Tooth 7'), (8, 'Tooth 8'), (9, 'Tooth 9'), (10, 'Tooth 10'), (11, 'Tooth 11'), (12, 'Tooth 12'), (13, 'Tooth 13'), (14, 'Tooth 14'), (15, 'Tooth 15'), (16, 'Tooth 16'), (17, 'Tooth 17'), (18, 'Tooth 18'), (19, 'Tooth 19'), (20, 'Tooth 20'), (21, 'Tooth 21'), (22, 'Tooth 22'), (23, 'Tooth 23'), (24, 'Tooth 24'), (25, 'Tooth 25'), (26, 'Tooth 26'), (27, 'Tooth 27'), (28, 'Tooth 28'), (29, 'Tooth 29'), (30, 'Tooth 30'), (31, 'Tooth 31'), (32, 'Tooth 32')])),
                ('xray_file', models.FileField(upload_to='xrays/')),
                ('diagnosis', models.TextField()),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='claims.patient')),
            ],
        ),
        migrations.CreateModel(
            name='CrownRecommendation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cdt_code', models.CharField(choices=[('D2740', 'Crown - porcelain/ceramic')], default='D2740', max_length=10)),
                ('reason', models.TextField(blank=True)),
                ('xray', models.FileField(blank=True, null=True, upload_to='claims/')),
                ('clinical_note', models.TextField(blank=True)),
                ('status', models.CharField(default='Pending', max_length=20)),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='claims.patient')),
                ('tooth', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='claims.toothrecord')),
            ],
        ),
    ]
