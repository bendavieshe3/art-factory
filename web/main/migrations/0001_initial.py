# Generated by Django 5.0.6 on 2024-06-06 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Warehouse",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("path", models.CharField(max_length=255)),
                ("is_default", models.BooleanField(default=False)),
            ],
        ),
    ]