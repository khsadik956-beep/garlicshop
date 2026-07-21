from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_remove_order_comment_remove_order_is_paid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('placed', 'Placed'),
                    ('processing', 'Processing'),
                    ('cancelled', 'Cancelled'),
                    ('return_requested', 'Return Requested'),
                ],
                default='placed',
                max_length=30,
            ),
        ),
    ]