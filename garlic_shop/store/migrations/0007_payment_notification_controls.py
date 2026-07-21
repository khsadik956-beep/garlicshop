import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_real_commerce_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('paid', 'Paid'),
                    ('failed', 'Failed'),
                    ('refunded', 'Refunded'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='gateway_order_id',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='order',
            name='gateway_payment_id',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='order',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='PaymentTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gateway', models.CharField(default='manual', max_length=50)),
                ('gateway_order_id', models.CharField(blank=True, default='', max_length=120)),
                ('gateway_payment_id', models.CharField(blank=True, default='', max_length=120)),
                ('amount', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('status', models.CharField(choices=[('created', 'Created'), ('success', 'Success'), ('failed', 'Failed'), ('refunded', 'Refunded')], default='created', max_length=20)),
                ('note', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='store.order')),
            ],
        ),
        migrations.CreateModel(
            name='NotificationLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.CharField(choices=[('system', 'System'), ('email', 'Email'), ('sms', 'SMS'), ('whatsapp', 'WhatsApp')], default='system', max_length=20)),
                ('recipient', models.CharField(max_length=150)),
                ('message', models.TextField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('queued', 'Queued'), ('sent', 'Sent'), ('failed', 'Failed')], default='queued', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='store.order')),
            ],
        ),
    ]
