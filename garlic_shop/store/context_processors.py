from urllib.parse import quote_plus

from django.conf import settings


def contact_settings(request):
    whatsapp_number = settings.WHATSAPP_PHONE_NUMBER
    whatsapp_text = "Hi GarlicShop, I want to know more about your garlic products."
    return {
        "whatsapp_number": whatsapp_number,
        "whatsapp_display_number": f"+{whatsapp_number[:2]} {whatsapp_number[2:]}",
        "whatsapp_url": f"https://wa.me/{whatsapp_number}?text={quote_plus(whatsapp_text)}",
    }
