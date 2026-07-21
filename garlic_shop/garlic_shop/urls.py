from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from store import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.home, name='home'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),

    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/buy-later/<int:product_id>/', views.move_to_buy_later, name='move_to_buy_later'),
    path('cart/buy-later/<int:product_id>/cart/', views.buy_later_to_cart, name='buy_later_to_cart'),
    path('cart/buy-later/<int:product_id>/remove/', views.remove_buy_later, name='remove_buy_later'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),

    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('account/profile/', views.account_profile, name='account_profile'),
    path('account/address/<int:address_id>/default/', views.set_default_address, name='set_default_address'),
    path('account/address/<int:address_id>/delete/', views.delete_address, name='delete_address'),

    path('checkout/', views.checkout_view, name='checkout'),
    path('success/', views.order_success, name='order_success'),

    path('my-orders/', views.my_orders_view, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),
    path('order/<int:order_id>/invoice/', views.invoice_pdf_view, name='invoice_pdf'),
    path('order/<int:order_id>/payment-success/', views.payment_success_view, name='payment_success'),
    path('order/<int:order_id>/return/', views.return_order, name='return_order'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('product/<int:product_id>/review/', views.submit_review, name='submit_review'),

    path('bulk-inquiry/', views.bulk_inquiry_view, name='bulk_inquiry'),
    path('subscriptions/', views.subscription_plans_view, name='subscription_plans'),
    path('subscriptions/<int:plan_id>/', views.subscription_request_view, name='subscription_request'),
    path('garlic-guide/', views.garlic_guide_view, name='garlic_guide'),
    path('policies/<str:policy_type>/', views.policy_page, name='policy_page'),

    path('shop-admin/', views.shop_admin_dashboard, name='shop_admin_dashboard'),
    path('shop-admin/products/', views.shop_admin_products, name='shop_admin_products'),
    path('shop-admin/products/add/', views.shop_admin_product_add, name='shop_admin_product_add'),
    path('shop-admin/products/<int:product_id>/edit/', views.shop_admin_product_edit, name='shop_admin_product_edit'),
    path('shop-admin/products/<int:product_id>/delete/', views.shop_admin_product_delete, name='shop_admin_product_delete'),
    path('shop-admin/orders/', views.shop_admin_orders, name='shop_admin_orders'),
    path('shop-admin/orders/export/', views.shop_admin_orders_export, name='shop_admin_orders_export'),
    path('shop-admin/orders/<int:order_id>/', views.shop_admin_order_detail, name='shop_admin_order_detail'),
    path('shop-admin/orders/<int:order_id>/packing-slip/', views.packing_slip_view, name='packing_slip'),
    path('shop-admin/orders/<int:order_id>/quick/<str:action>/', views.shop_admin_order_quick_action, name='shop_admin_order_quick_action'),
    path('shop-admin/inquiries/', views.shop_admin_inquiries, name='shop_admin_inquiries'),
    path('shop-admin/subscriptions/', views.shop_admin_subscriptions, name='shop_admin_subscriptions'),
    path('shop-admin/notifications/', views.shop_admin_notifications, name='shop_admin_notifications'),
    path('shop-admin/commerce/', views.shop_admin_commerce, name='shop_admin_commerce'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
