from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0007_payment_notification_controls"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="courier_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="order",
            name="tracking_number",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="order",
            name="expected_delivery_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
