from django.contrib import admin
from .models import (
    Product, ProductImage, WishlistItem, BuyLaterItem,
    CustomerProfile, CustomerAddress, Order, OrderItem, Review,
    PaymentTransaction, FarmTrackingStep, NotificationLog, ReturnRequest,
    BulkInquiry, Coupon, DeliveryZone,
    SubscriptionPlan, SubscriptionRequest
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "sku", "price", "stock_quantity", "low_stock_threshold",
        "category", "is_available", "aroma_level", "best_for"
    ]
    list_filter = ["is_available", "category", "brand", "aroma_level"]
    search_fields = ["name", "sku", "description", "category", "brand", "best_for"]
    inlines = [ProductImageInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class FarmTrackingStepInline(admin.TabularInline):
    model = FarmTrackingStep
    extra = 1


class PaymentTransactionInline(admin.TabularInline):
    model = PaymentTransaction
    extra = 0


class NotificationLogInline(admin.TabularInline):
    model = NotificationLog
    extra = 0


class ReturnRequestInline(admin.StackedInline):
    model = ReturnRequest
    extra = 0
    max_num = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id", "invoice_number", "user", "shipping_name", "shipping_phone",
        "delivery_pincode", "total_amount", "payment_method", "payment_status",
        "courier_name", "tracking_number", "status", "created_at"
    ]
    list_filter = ["payment_method", "payment_status", "status", "created_at"]
    search_fields = [
        "invoice_number", "shipping_name", "shipping_phone",
        "shipping_address", "delivery_pincode", "courier_name",
        "tracking_number", "user__username"
    ]
    inlines = [OrderItemInline, PaymentTransactionInline, FarmTrackingStepInline, ReturnRequestInline, NotificationLogInline]


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "order", "gateway", "amount", "status",
        "gateway_order_id", "gateway_payment_id", "created_at"
    ]
    list_filter = ["gateway", "status", "created_at"]
    search_fields = ["gateway_order_id", "gateway_payment_id", "order__invoice_number"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["product__name", "user__username", "comment"]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["user__username", "product__name"]


@admin.register(BuyLaterItem)
class BuyLaterItemAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "quantity", "created_at"]
    search_fields = ["user__username", "product__name"]


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "full_name", "phone", "updated_at"]
    search_fields = ["user__username", "full_name", "phone"]


@admin.register(CustomerAddress)
class CustomerAddressAdmin(admin.ModelAdmin):
    list_display = ["user", "label", "full_name", "phone", "pincode", "city", "state", "is_default"]
    list_filter = ["label", "state", "is_default"]
    search_fields = ["user__username", "full_name", "phone", "pincode", "city", "state"]


@admin.register(FarmTrackingStep)
class FarmTrackingStepAdmin(admin.ModelAdmin):
    list_display = ["order", "title", "step", "completed", "completed_at"]
    list_filter = ["step", "completed"]
    search_fields = ["title", "note", "order__id"]


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ["order", "channel", "recipient", "status", "created_at"]
    list_filter = ["channel", "status", "created_at"]
    search_fields = ["recipient", "message", "order__invoice_number"]


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ["order", "reason", "refund_mode", "status", "created_at"]
    list_filter = ["reason", "refund_mode", "status", "created_at"]
    search_fields = ["order__id", "order__invoice_number", "pickup_address", "note"]


@admin.register(BulkInquiry)
class BulkInquiryAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "business_type", "product_needed", "quantity", "city", "created_at"]
    search_fields = ["name", "phone", "city", "product_needed"]


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code", "discount_type", "discount_value", "min_order_amount",
        "max_discount", "is_active", "valid_from", "valid_to"
    ]
    list_filter = ["discount_type", "is_active"]
    search_fields = ["code"]


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = [
        "pincode_prefix", "city", "state", "delivery_charge",
        "free_delivery_above", "is_active"
    ]
    list_filter = ["state", "is_active"]
    search_fields = ["pincode_prefix", "city", "state"]


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "delivery_frequency", "is_active"]
    list_filter = ["is_active", "delivery_frequency"]
    search_fields = ["name", "description"]


@admin.register(SubscriptionRequest)
class SubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "plan", "created_at"]
    search_fields = ["name", "phone", "address"]
