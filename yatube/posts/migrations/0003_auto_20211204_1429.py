# Generated by Django 2.2.19 on 2021-12-04 11:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20211203_2302'),
    ]

    operations = [
        migrations.RenameField(
            model_name='group',
            old_name='slag',
            new_name='slug',
        ),
        migrations.AlterField(
            model_name='post',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group', to='posts.Group'),
        ),
    ]