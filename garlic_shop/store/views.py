import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Q, Sum
from django.core.mail import send_mail
from django.utils import timezone
from django.views.decorators.cache import never_cache
from decimal import Decimal

from .models import (
    Product, WishlistItem, BuyLaterItem, CustomerProfile, CustomerAddress,
    Order, OrderItem, Review,
    PaymentTransaction, FarmTrackingStep, NotificationLog,
    BulkInquiry, Coupon, DeliveryZone,
    SubscriptionPlan, SubscriptionRequest
)
from .forms import (
    ProductForm, CustomerProfileForm, CustomerAddressForm,
    OrderStatusForm, SubscriptionPlanForm,
    PaymentStatusForm, OrderLogisticsForm, TrackingStepForm, NotificationLogForm,
    CouponForm, DeliveryZoneForm
)


def calculate_checkout_totals(subtotal, pincode="", coupon_code=""):
    delivery_charge = Decimal("0.00")
    discount_amount = Decimal("0.00")
    applied_coupon = ""

    if pincode:
        zone = (
            DeliveryZone.objects.filter(is_active=True, pincode_prefix=pincode[:6]).first() or
            DeliveryZone.objects.filter(is_active=True, pincode_prefix=pincode[:3]).first()
        )
        if zone:
            delivery_charge = Decimal(str(zone.charge_for(subtotal)))

    coupon_code = coupon_code.strip().upper()
    if coupon_code:
        coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
        if coupon:
            discount_amount = Decimal(str(coupon.calculate_discount(subtotal)))
            if discount_amount > 0:
                applied_coupon = coupon.code

    total = max(Decimal("0.00"), subtotal + delivery_charge - discount_amount)
    return delivery_charge, discount_amount, applied_coupon, total


def simple_pdf_response(filename, lines):
    escaped_lines = []
    for line in lines:
        text = str(line).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        escaped_lines.append(text)

    y = 800
    stream_lines = ["BT", "/F1 11 Tf"]
    for line in escaped_lines:
        stream_lines.append(f"50 {y} Td ({line}) Tj")
        y = -16
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", errors="replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )

    response = HttpResponse(bytes(pdf), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def build_invoice_lines(order):
    lines = [
        "GarlicShop Invoice",
        f"Invoice: {order.invoice_number or 'Pending'}",
        f"Order: #GS-00{order.id}",
        f"Date: {order.created_at:%d %b %Y}",
        "",
        f"Customer: {order.shipping_name}",
        f"Phone: {order.shipping_phone}",
        f"Address: {order.shipping_address}",
        "",
        "Items:",
    ]
    for item in order.items.all():
        total = item.price * item.quantity
        lines.append(f"- {item.product.name} | Qty: {item.quantity} | Rs. {item.price} | Rs. {total}")

    lines.extend([
        "",
        f"Subtotal: Rs. {order.display_subtotal()}",
        f"Delivery: Rs. {order.delivery_charge}",
        f"Discount: Rs. {order.discount_amount}",
        f"Total: Rs. {order.total_amount}",
        f"Payment: {order.payment_method} / {order.get_payment_status_display()}",
    ])
    if order.courier_name or order.tracking_number or order.expected_delivery_date:
        lines.extend([
            "",
            "Delivery Tracking:",
            f"Courier: {order.courier_name or '-'}",
            f"Tracking Number: {order.tracking_number or '-'}",
            f"Expected Delivery: {order.expected_delivery_date or '-'}",
        ])
    return lines


def complete_tracking_step(order, step_key):
    step = order.tracking_steps.filter(step=step_key).first()
    if step:
        step.completed = True
        step.completed_at = timezone.now()
        step.save(update_fields=["completed", "completed_at"])


def queue_customer_notification(order, message, channel="system"):
    notification = NotificationLog.objects.create(
        order=order,
        channel=channel,
        recipient=order.shipping_phone or order.user.username,
        message=message,
        status="queued",
    )
    if channel == "email" and order.user.email:
        try:
            send_mail(
                subject=f"GarlicShop order #{order.id} update",
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.user.email],
                fail_silently=False,
            )
            notification.status = "sent"
            notification.save(update_fields=["status"])
        except Exception:
            notification.status = "failed"
            notification.save(update_fields=["status"])
    return notification


@never_cache
def home(request):
    non_garlic_categories = [
        "Farm Grains", "Millets", "Pulses", "Oil Seeds", "Spices",
        "Fresh Vegetables", "Fresh Herbs", "Farm Sweeteners",
        "Farm Dairy", "Farm Supplies", "Farm Seeds",
        "Natural Farm Produce", "Natural Grains", "Natural Pulses",
        "Natural Oilseeds", "Natural Greens", "Natural Farm Seeds",
        "Natural Flours", "Natural Oils", "Natural Sweeteners", "Dry Fruits",
        "Super Seeds", "Natural Snacks", "Natural Staples", "Herbal Products",
        "Natural Masala", "Natural Salts", "Natural Pickles", "Natural Papad",
        "Natural Combos",
    ]
    garlic_filter = (
        Q(name__icontains="garlic") |
        Q(category__icontains="garlic")
    )
    products = (
        Product.objects.filter(is_available=True)
        .filter(garlic_filter)
        .exclude(category__in=non_garlic_categories)
        .exclude(sku__startswith="GS-AGRI-")
        .exclude(sku__startswith="GS-NAT-")
        .exclude(sku__startswith="GS-RAW-")
    )
    categories = (
        Product.objects.filter(is_available=True)
        .filter(garlic_filter)
        .exclude(category__in=non_garlic_categories)
        .exclude(sku__startswith="GS-AGRI-")
        .exclude(sku__startswith="GS-NAT-")
        .exclude(sku__startswith="GS-RAW-")
        .exclude(category__isnull=True)
        .exclude(category="")
        .values_list("category", flat=True)
        .distinct()
        .order_by("category")
    )
    query = request.GET.get('q', '').strip()
    category = request.GET.get("category", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    sort = request.GET.get("sort", "latest").strip()

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query) |
            Q(brand__icontains=query) |
            Q(best_for__icontains=query)
        )

    if category:
        products = products.filter(category=category)

    try:
        if min_price:
            products = products.filter(price__gte=Decimal(min_price))
        if max_price:
            products = products.filter(price__lte=Decimal(max_price))
    except Exception:
        min_price = ""
        max_price = ""

    sort_options = {
        "latest": "-id",
        "price_low": "price",
        "price_high": "-price",
        "name": "name",
        "stock": "-stock_quantity",
    }
    products = list(products.order_by(sort_options.get(sort, "-id")).annotate(
        avg_rating=Avg("reviews__rating"),
        review_count=Count("reviews"),
    ))
    discount_cycle = [8, 10, 12, 15, 18, 20, 22, 25]
    rating_cycle = [4.4, 4.5, 4.6, 4.7, 4.8, 4.9]
    review_cycle = [11, 18, 24, 31, 42, 57, 73, 88]
    for index, product in enumerate(products):
        product.display_discount = discount_cycle[index % len(discount_cycle)]
        product.display_old_price = (product.price * 100 / (100 - product.display_discount)).quantize(Decimal("1"))
        product.display_rating = rating_cycle[index % len(rating_cycle)]
        product.display_review_count = product.review_count or review_cycle[index % len(review_cycle)]
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist_product_ids = list(
            WishlistItem.objects.filter(user=request.user).values_list("product_id", flat=True)
        )

    return render(request, 'store/home.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort,
        'wishlist_product_ids': wishlist_product_ids,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    reviews = product.reviews.all().order_by('-created_at')
    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = WishlistItem.objects.filter(user=request.user, product=product).exists()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'is_wishlisted': is_wishlisted,
    })


@login_required
def wishlist_view(request):
    wishlist_items = (
        WishlistItem.objects.select_related("product")
        .filter(user=request.user, product__is_available=True)
    )
    return render(request, "store/wishlist.html", {"wishlist_items": wishlist_items})


@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    wishlist_item = WishlistItem.objects.filter(user=request.user, product=product).first()
    if wishlist_item:
        wishlist_item.delete()
        messages.success(request, "Product wishlist se remove ho gaya.")
    else:
        WishlistItem.objects.create(user=request.user, product=product)
        messages.success(request, "Product wishlist me add ho gaya.")

    next_url = request.POST.get("next") or request.GET.get("next")
    return redirect(next_url or "wishlist")


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    if product.stock_quantity <= 0:
        messages.error(request, "Product abhi out of stock hai.")
        return redirect('home')

    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    next_quantity = cart.get(product_id_str, 0) + 1

    if next_quantity > product.stock_quantity:
        messages.error(request, "Is product ka available stock cart quantity se kam hai.")
        return redirect('cart_detail')

    cart[product_id_str] = next_quantity

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart_detail')


def update_cart(request, product_id):
    if request.method == "POST":
        cart = request.session.get('cart', {})
        quantity = int(request.POST.get('quantity', 1))
        product = get_object_or_404(Product, id=product_id, is_available=True)
        quantity = min(quantity, product.stock_quantity)

        if quantity > 0:
            cart[str(product_id)] = quantity
        else:
            cart.pop(str(product_id), None)

        request.session['cart'] = cart
        request.session.modified = True

    return redirect('cart_detail')


def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    cart.pop(str(product_id), None)

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart_detail')


@login_required
def move_to_buy_later(request, product_id):
    cart = request.session.get('cart', {})
    product_id_str = str(product_id)
    quantity = int(cart.get(product_id_str, 1) or 1)
    product = get_object_or_404(Product, id=product_id, is_available=True)
    item, created = BuyLaterItem.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={"quantity": max(1, quantity)},
    )
    if not created:
        item.quantity = max(item.quantity, quantity)
        item.save(update_fields=["quantity"])

    cart.pop(product_id_str, None)
    request.session["cart"] = cart
    request.session.modified = True
    messages.success(request, "Product Buy Later me save ho gaya.")
    return redirect("cart_detail")


@login_required
def buy_later_to_cart(request, product_id):
    item = get_object_or_404(BuyLaterItem, user=request.user, product_id=product_id)
    cart = request.session.get("cart", {})
    product_id_str = str(product_id)
    cart[product_id_str] = cart.get(product_id_str, 0) + item.quantity
    request.session["cart"] = cart
    request.session.modified = True
    item.delete()
    messages.success(request, "Product cart me move ho gaya.")
    return redirect("cart_detail")


@login_required
def remove_buy_later(request, product_id):
    BuyLaterItem.objects.filter(user=request.user, product_id=product_id).delete()
    messages.success(request, "Buy Later se product remove ho gaya.")
    return redirect("cart_detail")


def cart_detail(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(product_id), is_available=True)
        except (Product.DoesNotExist, ValueError):
            continue

        quantity = min(max(1, int(quantity)), product.stock_quantity)
        if quantity <= 0:
            continue
        sub_total = product.price * quantity
        total_price += sub_total

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'sub_total': sub_total,
        })

    buy_later_items = []
    if request.user.is_authenticated:
        buy_later_items = BuyLaterItem.objects.select_related("product").filter(
            user=request.user,
            product__is_available=True,
        )

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'buy_later_items': buy_later_items,
    })


def clear_cart(request):
    request.session['cart'] = {}
    request.session.modified = True
    return redirect('cart_detail')


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'store/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()

    return render(request, 'store/login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('home')


@login_required
def account_profile(request):
    profile, created = CustomerProfile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name": request.user.get_full_name() or request.user.username,
            "phone": "",
        },
    )
    address_id = request.GET.get("edit_address")
    editing_address = None
    if address_id:
        editing_address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "profile":
            profile_form = CustomerProfileForm(request.POST, instance=profile)
            address_form = CustomerAddressForm(instance=editing_address)
            if profile_form.is_valid():
                profile_form.save()
                request.user.first_name = profile_form.cleaned_data["full_name"].split(" ")[0]
                request.user.save(update_fields=["first_name"])
                messages.success(request, "Profile update ho gaya.")
                return redirect("account_profile")
        elif form_type == "address":
            editing_id = request.POST.get("address_id")
            address_instance = None
            if editing_id:
                address_instance = get_object_or_404(CustomerAddress, id=editing_id, user=request.user)
            profile_form = CustomerProfileForm(instance=profile)
            address_form = CustomerAddressForm(request.POST, instance=address_instance)
            if address_form.is_valid():
                address = address_form.save(commit=False)
                address.user = request.user
                address.save()
                messages.success(request, "Address save ho gaya.")
                return redirect("account_profile")
        else:
            return redirect("account_profile")
    else:
        profile_form = CustomerProfileForm(instance=profile)
        address_form = CustomerAddressForm(instance=editing_address, initial={
            "full_name": profile.full_name or request.user.username,
            "phone": profile.phone,
            "country": "India",
        })

    addresses = CustomerAddress.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by("-created_at")[:5]
    return render(request, "store/account_profile.html", {
        "profile_form": profile_form,
        "address_form": address_form,
        "addresses": addresses,
        "orders": orders,
        "editing_address": editing_address,
    })


@login_required
def set_default_address(request, address_id):
    if request.method == "POST":
        address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
        address.is_default = True
        address.save(update_fields=["is_default", "updated_at"])
        messages.success(request, "Default address set ho gaya.")
    return redirect("account_profile")


@login_required
def delete_address(request, address_id):
    if request.method == "POST":
        get_object_or_404(CustomerAddress, id=address_id, user=request.user).delete()
        messages.success(request, "Address delete ho gaya.")
    return redirect("account_profile")


@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('cart_detail')

    cart_items = []
    total_price = 0

    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(product_id), is_available=True)
        except (Product.DoesNotExist, ValueError):
            continue

        quantity = min(max(1, int(quantity)), product.stock_quantity)
        if quantity <= 0:
            continue
        item_total = product.price * quantity
        total_price += item_total

        cart_items.append({
            'product': product,
            'quantity': quantity,
            'price': product.price,
            'item_total': item_total,
        })

    if not cart_items:
        request.session['cart'] = {}
        request.session.modified = True
        return redirect('cart_detail')

    saved_addresses = CustomerAddress.objects.filter(user=request.user)
    default_address = saved_addresses.filter(is_default=True).first() or saved_addresses.first()

    if request.method == 'POST':
        pincode = request.POST.get('delivery_pincode', '').strip()
        coupon_code = request.POST.get('coupon_code', '').strip()
        delivery_charge, discount_amount, applied_coupon, final_total = calculate_checkout_totals(
            total_price, pincode, coupon_code
        )

        order = Order.objects.create(
            user=request.user,
            invoice_number="",
            shipping_name=request.POST.get('shipping_name') or request.user.username,
            shipping_phone=request.POST.get('shipping_phone') or "",
            shipping_address=request.POST.get('shipping_address') or "",
            delivery_pincode=pincode,
            order_note=request.POST.get('order_note') or "",
            subtotal_amount=total_price,
            delivery_charge=delivery_charge,
            discount_amount=discount_amount,
            coupon_code=applied_coupon,
            total_amount=final_total,
            payment_method=request.POST.get('payment_method') or "COD",
        )
        order.invoice_number = f"GS-{timezone.now():%Y%m%d}-{order.id:05d}"
        order.save(update_fields=["invoice_number"])

        PaymentTransaction.objects.create(
            order=order,
            gateway="cod" if order.payment_method == "COD" else "manual",
            amount=order.total_amount,
            status="created",
            note="Payment record created at checkout.",
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                quantity=item['quantity'],
                price=item['price'],
            )
            item['product'].stock_quantity = max(0, item['product'].stock_quantity - item['quantity'])
            item['product'].save(update_fields=["stock_quantity"])

        tracking_steps = [
            ("farm_selected", "Farm Selected", "Best farm batch selected for your order."),
            ("quality_checked", "Quality Checked", "Products checked for freshness and quality."),
            ("packed", "Packed", "Order packing will start soon."),
            ("shipped", "Shipped", "Waiting for dispatch."),
            ("delivered", "Delivered", "Delivery pending."),
        ]

        for index, (step, title, note) in enumerate(tracking_steps):
            FarmTrackingStep.objects.create(
                order=order,
                step=step,
                title=title,
                note=note,
                completed=index < 2,
                completed_at=timezone.now() if index < 2 else None,
            )

        queue_customer_notification(
            order,
            f"Order #{order.id} placed successfully. Total Rs. {order.total_amount}.",
            channel="email" if request.user.email else "system",
        )

        request.session['cart'] = {}
        request.session.modified = True

        if order.payment_method.upper() in {"RAZORPAY", "ONLINE", "UPI", "CARD"}:
            order.payment_method = "RAZORPAY"
            order.gateway_order_id = f"rzp_test_order_{order.id}"
            order.save(update_fields=["payment_method", "gateway_order_id"])
            order.payments.update(
                gateway="razorpay",
                gateway_order_id=order.gateway_order_id,
                note="Razorpay payment pending. Add live keys to enable gateway checkout.",
            )
            return render(request, "store/payment_pending.html", {
                "order": order,
                "gateway_enabled": settings.PAYMENT_GATEWAY_ENABLED and bool(settings.RAZORPAY_KEY_ID),
                "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            })

        return render(request, 'store/success.html', {'order': order})

    return render(request, 'store/checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'final_amount': total_price,
        'saved_addresses': saved_addresses,
        'default_address': default_address,
    })


def order_success(request):
    return render(request, 'store/success.html')


@login_required
def my_orders_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})


@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    return render(request, 'store/order_detail.html', {
        'order': order,
    })


@login_required
def invoice_pdf_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.user != request.user and not request.user.is_staff:
        raise Http404

    filename = f"invoice-{order.invoice_number or order.id}.pdf"
    return simple_pdf_response(filename, build_invoice_lines(order))


@login_required
def payment_success_view(request, order_id):
    if request.method != "POST":
        return redirect("order_detail", order_id=order_id)

    order = get_object_or_404(Order, id=order_id)
    if order.user != request.user and not request.user.is_staff:
        raise Http404

    order.payment_status = "paid"
    order.paid_at = timezone.now()
    order.gateway_payment_id = request.POST.get("gateway_payment_id") or f"manual-paid-{order.id}"
    order.save(update_fields=["payment_status", "paid_at", "gateway_payment_id"])

    PaymentTransaction.objects.create(
        order=order,
        gateway=order.payment_method.lower(),
        gateway_order_id=order.gateway_order_id,
        gateway_payment_id=order.gateway_payment_id,
        amount=order.total_amount,
        status="success",
        note="Payment marked successful. Replace with verified Razorpay callback in production.",
    )
    queue_customer_notification(order, f"Payment received for order #{order.id}. Total Rs. {order.total_amount}.")
    messages.success(request, "Payment successful mark ho gaya.")
    return redirect("order_detail", order_id=order.id)


@login_required
def cancel_order(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order.status = "cancelled"
        order.save()

        FarmTrackingStep.objects.create(
            order=order,
            step="cancelled",
            title="Order Cancelled",
            note="Customer cancelled this order.",
            completed=True,
            completed_at=timezone.now(),
        )

    return redirect('order_detail', order_id=order_id)


@login_required
def return_order(request, order_id):
    if request.method == "POST":
        order = get_object_or_404(Order, id=order_id, user=request.user)
        order.status = "return_requested"
        order.save()

        FarmTrackingStep.objects.create(
            order=order,
            step="return_requested",
            title="Return Requested",
            note="Customer requested a return for this order.",
            completed=True,
            completed_at=timezone.now(),
        )

    return redirect('order_detail', order_id=order_id)


@login_required
def submit_review(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)

        Review.objects.create(
            product=product,
            user=request.user,
            rating=int(request.POST.get('rating', 5)),
            comment=request.POST.get('comment'),
            image=request.FILES.get('review_image'),
            video=request.FILES.get('review_video'),
        )

        messages.success(request, "Aapka review successfully post ho gaya hai!")
        return redirect('product_detail', product_id=product.id)

    return redirect('home')


def bulk_inquiry_view(request):
    if request.method == "POST":
        BulkInquiry.objects.create(
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            business_type=request.POST.get("business_type"),
            product_needed=request.POST.get("product_needed"),
            quantity=request.POST.get("quantity"),
            city=request.POST.get("city"),
            message=request.POST.get("message"),
        )

        messages.success(request, "Bulk inquiry receive ho gayi hai. Team jaldi contact karegi.")
        return redirect("bulk_inquiry")

    return render(request, "store/bulk_inquiry.html")


def subscription_plans_view(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, "store/subscription_plans.html", {"plans": plans})


def subscription_request_view(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id, is_active=True)

    if request.method == "POST":
        SubscriptionRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            plan=plan,
            name=request.POST.get("name"),
            phone=request.POST.get("phone"),
            address=request.POST.get("address"),
        )

        messages.success(request, "Subscription request receive ho gayi hai.")
        return redirect("subscription_plans")

    return render(request, "store/subscription_request.html", {"plan": plan})


def garlic_guide_view(request):
    products = Product.objects.filter(is_available=True)
    purpose = request.GET.get("purpose", "")
    guide_filters = {
        "daily": ["daily", "fresh garlic", "whole", "family kitchen", "quick cooking"],
        "restaurant": ["restaurant", "bulk", "hotels", "resellers", "snacks"],
        "pickle": ["pickle", "tangy", "spicy"],
        "bulk": ["bulk", "5kg", "hotels", "resellers", "supply"],
        "farming": ["seed", "farming", "garden"],
        "powder": ["powder", "seasoning", "marinades"],
    }

    if purpose in guide_filters:
        product_filter = Q()
        for keyword in guide_filters[purpose]:
            product_filter |= (
                Q(name__icontains=keyword) |
                Q(description__icontains=keyword) |
                Q(category__icontains=keyword) |
                Q(form_factor__icontains=keyword) |
                Q(taste_profile__icontains=keyword) |
                Q(best_for__icontains=keyword)
            )
        products = products.filter(product_filter).distinct()

    return render(request, "store/garlic_guide.html", {
        "products": products,
        "purpose": purpose,
    })


def policy_page(request, policy_type):
    policies = {
        "privacy": {
            "title": "Privacy Policy",
            "intro": "GarlicShop customer data ko order processing, support aur delivery ke liye use karta hai.",
            "points": [
                "Name, phone, address aur order details checkout aur delivery ke liye store hote hain.",
                "Payment details gateway provider ke secure system par process hote hain; card data GarlicShop store nahi karta.",
                "Customer support ke liye WhatsApp, email ya phone par contact kiya ja sakta hai.",
                "Data ko law, fraud prevention aur business records ke liye required period tak rakha ja sakta hai.",
            ],
        },
        "refund": {
            "title": "Refund & Return Policy",
            "intro": "Fresh food products ke liye return/refund product condition aur delivery issue par depend karta hai.",
            "points": [
                "Damaged, wrong, ya missing item ke liye delivery ke 24 hours ke andar support se contact karein.",
                "Fresh garlic products opened/used hone ke baad normal return accept nahi hota.",
                "Approved refund original payment mode ya store credit ke through process hoga.",
                "Cancellation dispatch se pehle allowed hai; shipped orders ke liye support review karega.",
            ],
        },
        "terms": {
            "title": "Terms & Conditions",
            "intro": "GarlicShop use karne par aap website ke order, delivery aur payment terms accept karte hain.",
            "points": [
                "Product images indicative hain; fresh produce size/color batch ke hisaab se vary kar sakta hai.",
                "Prices, offers aur stock availability without prior notice change ho sakte hain.",
                "Customer ko correct phone, address aur pincode provide karna zaroori hai.",
                "Bulk/subscription requests final confirmation ke baad process honge.",
            ],
        },
    }
    policy = policies.get(policy_type)
    if not policy:
        raise Http404
    return render(request, "store/policy.html", {"policy": policy})


def robots_txt(request):
    sitemap_url = request.build_absolute_uri("/sitemap.xml")
    content = "\n".join([
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {sitemap_url}",
    ])
    return HttpResponse(content, content_type="text/plain")


def sitemap_xml(request):
    static_paths = [
        "",
        "bulk-inquiry/",
        "subscriptions/",
        "garlic-guide/",
        "policies/privacy/",
        "policies/refund/",
        "policies/terms/",
    ]
    urls = [request.build_absolute_uri(f"/{path}") for path in static_paths]
    for product in Product.objects.filter(is_available=True).order_by("id"):
        urls.append(request.build_absolute_uri(f"/product/{product.id}/"))

    xml_urls = "\n".join(
        f"  <url><loc>{url}</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>"
        for url in urls
    )
    xml = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{xml_urls}\n</urlset>'
    return HttpResponse(xml, content_type="application/xml")

def staff_required(view_func):
    staff_check = user_passes_test(lambda user: user.is_staff, login_url="login")
    return login_required(staff_check(view_func), login_url="login")


@staff_required
def shop_admin_dashboard(request):
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_available=True).count()
    low_stock_products = Product.objects.filter(stock_quantity__lte=5).order_by("stock_quantity")[:8]
    total_orders = Order.objects.count()
    pending_orders = Order.objects.exclude(status__in=["cancelled", "return_requested"]).count()
    total_revenue = Order.objects.exclude(status="cancelled").aggregate(total=Sum("total_amount"))["total"] or 0
    bulk_inquiries = BulkInquiry.objects.order_by("-created_at")[:5]
    latest_orders = Order.objects.order_by("-created_at")[:6]

    return render(request, "store/shop_admin/dashboard.html", {
        "total_products": total_products,
        "active_products": active_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_revenue": total_revenue,
        "low_stock_products": low_stock_products,
        "bulk_inquiries": bulk_inquiries,
        "latest_orders": latest_orders,
    })


@staff_required
def shop_admin_products(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.order_by("-id")

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(category__icontains=query) |
            Q(brand__icontains=query)
        )

    return render(request, "store/shop_admin/products.html", {
        "products": products,
        "query": query,
    })


@staff_required
def shop_admin_product_add(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product add ho gaya.")
            return redirect("shop_admin_products")
    else:
        form = ProductForm()

    return render(request, "store/shop_admin/product_form.html", {
        "form": form,
        "title": "Add Product",
        "button_text": "Save Product",
    })


@staff_required
def shop_admin_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product update ho gaya.")
            return redirect("shop_admin_products")
    else:
        form = ProductForm(instance=product)

    return render(request, "store/shop_admin/product_form.html", {
        "form": form,
        "product": product,
        "title": "Edit Product",
        "button_text": "Update Product",
    })


@staff_required
def shop_admin_product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        product.delete()
        messages.success(request, "Product delete ho gaya.")
        return redirect("shop_admin_products")

    return render(request, "store/shop_admin/delete_confirm.html", {
        "object_name": product.name,
        "cancel_url": "shop_admin_products",
    })


@staff_required
def shop_admin_orders(request):
    status = request.GET.get("status", "").strip()
    orders = Order.objects.select_related("user").order_by("-created_at")

    if status:
        orders = orders.filter(status=status)

    return render(request, "store/shop_admin/orders.html", {
        "orders": orders,
        "status": status,
        "status_choices": Order.STATUS_CHOICES,
    })


@staff_required
def shop_admin_orders_export(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="garlicshop-orders.csv"'
    writer = csv.writer(response)
    writer.writerow([
        "Order ID", "Invoice", "Customer", "Phone", "Address", "Total",
        "Payment Method", "Payment Status", "Order Status", "Courier",
        "Tracking Number", "Date",
    ])
    for order in Order.objects.select_related("user").order_by("-created_at"):
        writer.writerow([
            f"GS-00{order.id}",
            order.invoice_number,
            order.shipping_name or order.user.username,
            order.shipping_phone,
            order.shipping_address,
            order.total_amount,
            order.payment_method,
            order.get_payment_status_display(),
            order.get_status_display(),
            order.courier_name,
            order.tracking_number,
            order.created_at.strftime("%d %b %Y %H:%M"),
        ])
    return response


@staff_required
def shop_admin_order_quick_action(request, order_id, action):
    order = get_object_or_404(Order, id=order_id)
    allowed_actions = {
        "processing": "processing",
        "packed": "packed",
        "shipped": "shipped",
        "delivered": "delivered",
        "cancelled": "cancelled",
        "return_requested": "return_requested",
    }
    if request.method == "POST" and action in allowed_actions:
        order.status = allowed_actions[action]
        order.save(update_fields=["status"])
        status_to_step = {
            "packed": "packed",
            "shipped": "shipped",
            "delivered": "delivered",
            "cancelled": "cancelled",
            "return_requested": "return_requested",
        }
        if order.status in status_to_step:
            complete_tracking_step(order, status_to_step[order.status])
        queue_customer_notification(order, f"Order #{order.id} status updated: {order.get_status_display()}.")
        messages.success(request, f"Order #{order.id} {order.get_status_display()} mark ho gaya.")
    return redirect(request.POST.get("next") or "shop_admin_orders")


@staff_required
def packing_slip_view(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items__product"), id=order_id)
    return render(request, "store/shop_admin/packing_slip.html", {"order": order})


@staff_required
def shop_admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "status":
            form = OrderStatusForm(request.POST, instance=order)
            if form.is_valid():
                updated_order = form.save()
                status_to_step = {
                    "packed": "packed",
                    "shipped": "shipped",
                    "delivered": "delivered",
                    "cancelled": "cancelled",
                    "return_requested": "return_requested",
                }
                if updated_order.status in status_to_step:
                    complete_tracking_step(updated_order, status_to_step[updated_order.status])
                queue_customer_notification(
                    updated_order,
                    f"Order #{updated_order.id} status updated: {updated_order.get_status_display()}.",
                )
                messages.success(request, "Order status update ho gaya.")
                return redirect("shop_admin_order_detail", order_id=order.id)
        elif form_type == "payment":
            payment_form = PaymentStatusForm(request.POST, instance=order)
            if payment_form.is_valid():
                updated_order = payment_form.save(commit=False)
                if updated_order.payment_status == "paid" and not updated_order.paid_at:
                    updated_order.paid_at = timezone.now()
                updated_order.save()
                PaymentTransaction.objects.create(
                    order=updated_order,
                    gateway=updated_order.payment_method.lower(),
                    gateway_order_id=updated_order.gateway_order_id,
                    gateway_payment_id=updated_order.gateway_payment_id,
                    amount=updated_order.total_amount,
                    status={
                        "paid": "success",
                        "pending": "created",
                        "failed": "failed",
                        "refunded": "refunded",
                    }[updated_order.payment_status],
                    note="Payment status updated from shop admin.",
                )
                queue_customer_notification(
                    updated_order,
                    f"Order #{updated_order.id} payment status: {updated_order.get_payment_status_display()}.",
                )
                messages.success(request, "Payment status update ho gaya.")
                return redirect("shop_admin_order_detail", order_id=order.id)
        elif form_type == "logistics":
            logistics_form = OrderLogisticsForm(request.POST, instance=order)
            if logistics_form.is_valid():
                updated_order = logistics_form.save()
                if updated_order.tracking_number:
                    note = f"Tracking number {updated_order.tracking_number}"
                    if updated_order.courier_name:
                        note += f" via {updated_order.courier_name}"
                    if updated_order.expected_delivery_date:
                        note += f". Expected delivery: {updated_order.expected_delivery_date:%d %b %Y}"
                    step, created = FarmTrackingStep.objects.get_or_create(
                        order=updated_order,
                        step="shipped",
                        title="Shipped",
                        defaults={
                            "note": note,
                            "completed": True,
                            "completed_at": timezone.now(),
                        },
                    )
                    if not created:
                        step.note = note
                        step.completed = True
                        if not step.completed_at:
                            step.completed_at = timezone.now()
                        step.save(update_fields=["note", "completed", "completed_at"])
                    queue_customer_notification(updated_order, f"Order #{updated_order.id} shipped. {note}")
                messages.success(request, "Delivery tracking details save ho gayi.")
                return redirect("shop_admin_order_detail", order_id=order.id)
        elif form_type == "tracking":
            tracking_form = TrackingStepForm(request.POST)
            if tracking_form.is_valid():
                tracking = tracking_form.save(commit=False)
                tracking.order = order
                if tracking.completed and not tracking.completed_at:
                    tracking.completed_at = timezone.now()
                tracking.save()
                messages.success(request, "Tracking step add ho gaya.")
                return redirect("shop_admin_order_detail", order_id=order.id)
        elif form_type == "notification":
            notification_form = NotificationLogForm(request.POST)
            if notification_form.is_valid():
                notification = notification_form.save(commit=False)
                notification.order = order
                notification.save()
                messages.success(request, "Notification log add ho gaya.")
                return redirect("shop_admin_order_detail", order_id=order.id)

    form = OrderStatusForm(instance=order)
    payment_form = PaymentStatusForm(instance=order)
    logistics_form = OrderLogisticsForm(instance=order)
    tracking_form = TrackingStepForm()
    notification_form = NotificationLogForm(initial={
        "recipient": order.shipping_phone,
        "message": f"Order #{order.id} update: {order.get_status_display()}",
        "status": "queued",
    })

    return render(request, "store/shop_admin/order_detail.html", {
        "order": order,
        "form": form,
        "payment_form": payment_form,
        "logistics_form": logistics_form,
        "tracking_form": tracking_form,
        "notification_form": notification_form,
    })


@staff_required
def shop_admin_inquiries(request):
    inquiries = BulkInquiry.objects.order_by("-created_at")
    return render(request, "store/shop_admin/inquiries.html", {"inquiries": inquiries})


@staff_required
def shop_admin_subscriptions(request):
    plans = SubscriptionPlan.objects.order_by("-id")
    requests = SubscriptionRequest.objects.select_related("plan", "user").order_by("-created_at")

    if request.method == "POST":
        form = SubscriptionPlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subscription plan add ho gaya.")
            return redirect("shop_admin_subscriptions")
    else:
        form = SubscriptionPlanForm()

    return render(request, "store/shop_admin/subscriptions.html", {
        "plans": plans,
        "requests": requests,
        "form": form,
    })


@staff_required
def shop_admin_notifications(request):
    if request.method == "POST":
        notification_id = request.POST.get("notification_id")
        status = request.POST.get("status")
        if status in dict(NotificationLog.STATUS_CHOICES):
            NotificationLog.objects.filter(id=notification_id).update(status=status)
            messages.success(request, "Notification status update ho gaya.")
        return redirect("shop_admin_notifications")

    notifications = NotificationLog.objects.select_related("order", "order__user").order_by("-created_at")[:100]
    return render(request, "store/shop_admin/notifications.html", {
        "notifications": notifications,
        "status_choices": NotificationLog.STATUS_CHOICES,
    })


@staff_required
def shop_admin_commerce(request):
    coupons = Coupon.objects.order_by("-id")
    zones = DeliveryZone.objects.order_by("pincode_prefix")

    coupon_form = CouponForm(prefix="coupon")
    zone_form = DeliveryZoneForm(prefix="zone")

    if request.method == "POST":
        if request.POST.get("form_type") == "coupon":
            coupon_form = CouponForm(request.POST, prefix="coupon")
            if coupon_form.is_valid():
                coupon_form.save()
                messages.success(request, "Coupon add ho gaya.")
                return redirect("shop_admin_commerce")
        elif request.POST.get("form_type") == "zone":
            zone_form = DeliveryZoneForm(request.POST, prefix="zone")
            if zone_form.is_valid():
                zone_form.save()
                messages.success(request, "Delivery zone add ho gaya.")
                return redirect("shop_admin_commerce")

    return render(request, "store/shop_admin/commerce.html", {
        "coupons": coupons,
        "zones": zones,
        "coupon_form": coupon_form,
        "zone_form": zone_form,
    })



