# GarlicShop Production Checklist

1. Set environment variables from `.env.example`.
2. Use PostgreSQL through `DATABASE_URL`.
3. Set `DJANGO_DEBUG=False`.
4. Set `DJANGO_ALLOWED_HOSTS` to the real domain.
5. Run `python manage.py collectstatic`.
6. Run `python manage.py migrate`.
7. Create a superuser.
8. Add Razorpay keys and turn on `PAYMENT_GATEWAY_ENABLED=True` after testing.
9. Configure SMTP email credentials.
10. Point the domain DNS to hosting.
11. Serve media files from hosting storage or cloud storage.
12. Test checkout, order tracking, invoice PDF, policy pages, and WhatsApp link.
13. Replace the temporary `payment_success_view` manual success action with Razorpay signature verification/webhook before accepting live payments.
14. Add a real SMS/WhatsApp Business provider if automatic customer messages are required.
15. Back up PostgreSQL and media files daily.
