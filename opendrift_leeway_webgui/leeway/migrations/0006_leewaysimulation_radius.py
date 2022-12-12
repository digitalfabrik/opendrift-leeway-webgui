# pylint: disable=invalid-name
# Generated by Django 3.2.16 on 2022-12-07 10:10

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Migration to add the radius field to the simulation model
    """

    dependencies = [("leeway", "0005_leewaysimulation_uuid")]

    operations = [
        migrations.AddField(
            model_name="leewaysimulation",
            name="radius",
            field=models.IntegerField(default=1000),
        )
    ]
