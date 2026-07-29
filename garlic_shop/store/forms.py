from django import forms
from .models import (
    Product, Order, FarmTrackingStep, NotificationLog,
    CustomerProfile, CustomerAddress, ReturnRequest,
    SubscriptionPlan, Coupon, DeliveryZone
)


class ProductForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "is_available":
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = Product
        fields = [
            "sku", "name", "price", "image", "is_available", "stock_quantity",
            "low_stock_threshold", "description", "category",
            "brand", "pack_of", "form_factor", "container_type", "highlights",
            "harvest_date", "packed_date", "shelf_life_days", "aroma_level",
            "taste_profile", "best_for",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "highlights": forms.Textarea(attrs={"rows": 4}),
            "harvest_date": forms.DateInput(attrs={"type": "date"}),
            "packed_date": forms.DateInput(attrs={"type": "date"}),
        }


class CustomerProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = CustomerProfile
        fields = ["full_name", "phone"]


class CustomerAddressForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "is_default":
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})
        self.fields["label"].widget.attrs.update({"class": "form-select"})

    class Meta:
        model = CustomerAddress
        fields = [
            "label", "full_name", "phone", "pincode", "address_line",
            "area", "city", "state", "country", "is_default",
        ]
        widgets = {
            "address_line": forms.Textarea(attrs={"rows": 3}),
        }


class OrderStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["status"].widget.attrs.update({"class": "form-select"})

    class Meta:
        model = Order
        fields = ["status"]


class PaymentStatusForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
        self.fields["payment_status"].widget.attrs.update({"class": "form-select"})

    class Meta:
        model = Order
        fields = ["payment_status", "gateway_order_id", "gateway_payment_id"]


class OrderLogisticsForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = Order
        fields = ["courier_name", "tracking_number", "expected_delivery_date"]
        widgets = {
            "expected_delivery_date": forms.DateInput(attrs={"type": "date"}),
        }


class TrackingStepForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "completed":
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = FarmTrackingStep
        fields = ["step", "title", "note", "completed"]
        widgets = {
            "note": forms.Textarea(attrs={"rows": 3}),
        }


class ReturnRequestForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name in ["reason", "refund_mode"]:
                field.widget.attrs.update({"class": "form-select"})
            else:
                field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = ReturnRequest
        fields = ["reason", "pickup_address", "refund_mode", "photo", "note"]
        widgets = {
            "pickup_address": forms.Textarea(attrs={"rows": 3}),
            "note": forms.Textarea(attrs={"rows": 4}),
        }


class NotificationLogForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({"class": "form-control"})
        self.fields["channel"].widget.attrs.update({"class": "form-select"})
        self.fields["status"].widget.attrs.update({"class": "form-select"})

    class Meta:
        model = NotificationLog
        fields = ["channel", "recipient", "message", "status"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 4}),
        }


class SubscriptionPlanForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "is_active":
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = SubscriptionPlan
        fields = ["name", "description", "price", "delivery_frequency", "is_active"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
        }


class CouponForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "is_active":
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = Coupon
        fields = [
            "code", "discount_type", "discount_value", "min_order_amount",
            "max_discount", "is_active", "valid_from", "valid_to",
        ]
        widgets = {
            "valid_from": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "valid_to": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class DeliveryZoneForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name == "is_active":
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})

    class Meta:
        model = DeliveryZone
        fields = [
            "pincode_prefix", "city", "state", "delivery_charge",
            "free_delivery_above", "is_active",
        ]

