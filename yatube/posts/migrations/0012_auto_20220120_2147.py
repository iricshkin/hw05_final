# Generated by Django 2.2.16 on 2022-01-20 21:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_auto_20220120_1955'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-created', '-pk'), 'verbose_name': 'Пост', 'verbose_name_plural': 'Посты'},
        ),
    ]
