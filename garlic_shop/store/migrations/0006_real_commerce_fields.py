from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_alter_farmtrackingstep_step'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(blank=True, max_length=60, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='product',
            name='stock_quantity',
            field=models.PositiveIntegerField(default=100),
        ),
        migrations.AddField(
            model_name='product',
            name='low_stock_threshold',
            field=models.PositiveIntegerField(default=5),
        ),
        migrations.AddField(
            model_name='order',
            name='invoice_number',
            field=models.CharField(blank=True, default='', max_length=40),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_pincode',
            field=models.CharField(blank=True, default='', max_length=6),
        ),
        migrations.AddField(
            model_name='order',
            name='subtotal_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_charge',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='order',
            name='discount_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name='order',
            name='coupon_code',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('placed', 'Placed'),
                    ('processing', 'Processing'),
                    ('packed', 'Packed'),
                    ('shipped', 'Shipped'),
                    ('delivered', 'Delivered'),
                    ('cancelled', 'Cancelled'),
                    ('return_requested', 'Return Requested'),
                ],
                default='placed',
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('discount_type', models.CharField(choices=[('flat', 'Flat Amount'), ('percent', 'Percentage')], default='flat', max_length=20)),
                ('discount_value', models.DecimalField(decimal_places=2, max_digits=10)),
                ('min_order_amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('max_discount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('valid_from', models.DateTimeField(blank=True, null=True)),
                ('valid_to', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryZone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pincode_prefix', models.CharField(max_length=6, unique=True)),
                ('city', models.CharField(blank=True, default='', max_length=100)),
                ('state', models.CharField(blank=True, default='', max_length=100)),
                ('delivery_charge', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('free_delivery_above', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
    ]
