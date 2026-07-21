from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Product(models.Model):
    sku = models.CharField(max_length=60, unique=True, null=True, blank=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=100)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    brand = models.CharField(max_length=100, default="Garlic Shop", null=True, blank=True)
    pack_of = models.CharField(max_length=50, default="1", null=True, blank=True)
    form_factor = models.CharField(max_length=100, help_text="Powder, Whole, etc.", null=True, blank=True)
    container_type = models.CharField(max_length=100, help_text="Bottle, Pouch, etc.", null=True, blank=True)
    highlights = models.TextField(help_text="Har line ke baad enter dabayein", null=True, blank=True)
    harvest_date = models.DateField(null=True, blank=True)
    packed_date = models.DateField(null=True, blank=True)
    shelf_life_days = models.IntegerField(default=30)
    aroma_level = models.CharField(max_length=50, default="Strong")
    taste_profile = models.CharField(max_length=100, default="Fresh and bold")
    best_for = models.CharField(max_length=200, default="Daily cooking")

    def freshness_score(self):
        if not self.packed_date:
            return 90

        days_old = (timezone.now().date() - self.packed_date).days
        score = 100 - int((days_old / max(self.shelf_life_days, 1)) * 100)
        return max(0, min(100, score))

    def is_in_stock(self):
        return self.is_available and self.stock_quantity > 0

    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/multiple/')

    def __str__(self):
        return f"{self.product.name} - Image"


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="wishlisted_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile")
    full_name = models.CharField(max_length=150, blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.user.username


class CustomerAddress(models.Model):
    ADDRESS_TYPE_CHOICES = [
        ("home", "Home"),
        ("work", "Work"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default="home")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    pincode = models.CharField(max_length=6)
    address_line = models.TextField()
    area = models.CharField(max_length=150, blank=True, default="")
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=80, default="India")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-updated_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            CustomerAddress.objects.filter(user=self.user, is_default=True).exclude(id=self.id).update(is_default=False)

    def formatted_address(self):
        parts = [self.address_line, self.area, self.city, self.state, self.country]
        return ", ".join([part for part in parts if part])

    def __str__(self):
        return f"{self.full_name} - {self.pincode}"


class BuyLaterItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="buy_later_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="buy_later_by")
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("placed", "Placed"),
        ("processing", "Processing"),
        ("packed", "Packed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("return_requested", "Return Requested"),
    ]

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=40, blank=True, default="")
    shipping_name = models.CharField(max_length=255, default="")
    shipping_phone = models.CharField(max_length=20, default="")
    shipping_address = models.TextField(default="")
    delivery_pincode = models.CharField(max_length=6, blank=True, default="")
    order_note = models.TextField(blank=True, null=True, default="")
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    coupon_code = models.CharField(max_length=50, blank=True, default="")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    payment_method = models.CharField(max_length=50, default="COD")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending")
    gateway_order_id = models.CharField(max_length=120, blank=True, default="")
    gateway_payment_id = models.CharField(max_length=120, blank=True, default="")
    paid_at = models.DateTimeField(null=True, blank=True)
    courier_name = models.CharField(max_length=120, blank=True, default="")
    tracking_number = models.CharField(max_length=120, blank=True, default="")
    expected_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="placed")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username}"

    def items_total(self):
        return sum(item.price * item.quantity for item in self.items.all())

    def display_subtotal(self):
        return self.subtotal_amount or self.items_total()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class PaymentTransaction(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    gateway = models.CharField(max_length=50, default="manual")
    gateway_order_id = models.CharField(max_length=120, blank=True, default="")
    gateway_payment_id = models.CharField(max_length=120, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.gateway} payment for order #{self.order_id}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='reviews/', null=True, blank=True)
    video = models.FileField(upload_to='reviews/videos/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.rating} stars)"


class FarmTrackingStep(models.Model):
    STEP_CHOICES = [
        ("farm_selected", "Farm Selected"),
        ("harvested", "Harvested"),
        ("cleaned", "Cleaned"),
        ("quality_checked", "Quality Checked"),
        ("packed", "Packed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("return_requested", "Return Requested"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="tracking_steps")
    step = models.CharField(max_length=50, choices=STEP_CHOICES)
    title = models.CharField(max_length=120)
    note = models.TextField(blank=True, null=True)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.order.id} - {self.title}"


class NotificationLog(models.Model):
    CHANNEL_CHOICES = [
        ("system", "System"),
        ("email", "Email"),
        ("sms", "SMS"),
        ("whatsapp", "WhatsApp"),
    ]

    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="notifications")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default="system")
    recipient = models.CharField(max_length=150)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.channel} notification for order #{self.order_id}"


class BulkInquiry(models.Model):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    business_type = models.CharField(max_length=100, blank=True, null=True)
    product_needed = models.CharField(max_length=150)
    quantity = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.product_needed}"


class Coupon(models.Model):
    DISCOUNT_CHOICES = [
        ("flat", "Flat Amount"),
        ("percent", "Percentage"),
    ]

    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES, default="flat")
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)

    def clean_code(self):
        return self.code.strip().upper()

    def is_valid_now(self, subtotal):
        now = timezone.now()
        if not self.is_active or subtotal < self.min_order_amount:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True

    def calculate_discount(self, subtotal):
        if not self.is_valid_now(subtotal):
            return 0
        if self.discount_type == "percent":
            discount = subtotal * self.discount_value / 100
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return discount
        return min(self.discount_value, subtotal)

    def save(self, *args, **kwargs):
        self.code = self.clean_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class DeliveryZone(models.Model):
    pincode_prefix = models.CharField(max_length=6, unique=True)
    city = models.CharField(max_length=100, blank=True, default="")
    state = models.CharField(max_length=100, blank=True, default="")
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    free_delivery_above = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_active = models.BooleanField(default=True)

    def charge_for(self, subtotal):
        if self.free_delivery_above and subtotal >= self.free_delivery_above:
            return 0
        return self.delivery_charge

    def __str__(self):
        label = self.pincode_prefix
        if self.city:
            label = f"{label} - {self.city}"
        return label


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_frequency = models.CharField(max_length=80, default="Monthly")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class SubscriptionRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.plan.name}"
