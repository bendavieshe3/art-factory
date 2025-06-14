# Generated by Django 5.2.1 on 2025-06-02 10:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_change_orderitem_product_cascade_to_set_null'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='batch_size',
            field=models.PositiveIntegerField(default=1, help_text='Number of products per API call'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='batches_completed',
            field=models.PositiveIntegerField(default=0, help_text='Number of completed batches'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='total_quantity',
            field=models.PositiveIntegerField(default=1, help_text='Total number of products to generate'),
        ),
        migrations.AddField(
            model_name='product',
            name='order_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='main.orderitem'),
        ),
    ]
