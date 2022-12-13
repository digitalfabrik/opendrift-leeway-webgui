# pylint: disable=invalid-name
# Generated by Django 4.1.4 on 2022-12-13 19:21

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Migration to add traceback field to the simulation model
    """

    dependencies = [("leeway", "0007_leewaysimulation_add_file_fields")]

    operations = [
        migrations.AddField(
            model_name="leewaysimulation",
            name="traceback",
            field=models.TextField(blank=True, verbose_name="traceback"),
        )
    ]