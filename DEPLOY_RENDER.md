# GarlicShop Online Launch

## Local Windows test

Sabse easy local start ke liye project root se ye file double-click karein:

```text
start-local.bat
```

Ya PowerShell me:

```powershell
.\start-local.ps1
```

PowerShell me `gunicorn` ke bajay production-style local test ke liye ye command use karein:

```powershell
pip install -r requirements.txt
python -m waitress --listen=127.0.0.1:8001 garlic_shop.wsgi:application
```

Agar aap normal development test kar rahe hain to ye bhi theek hai:

```powershell
cd garlic_shop
python manage.py runserver 8001
```

Website open hogi:

```text
http://127.0.0.1:8001/
```

## Render par online karna

1. Git install nahi hai to pehle Git for Windows install karein.
2. Project ko GitHub par push karein.
3. Render me New > Blueprint select karein.
4. GitHub repo connect karein.
5. Render `render.yaml` ko read karke web app aur PostgreSQL database bana dega.
6. Deploy complete hone ke baad Shell me run karein:

```bash
python garlic_shop/manage.py createsuperuser
```

## Required live settings

Render Environment me ye values check karein:

```text
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=auto generated
DATABASE_URL=Render PostgreSQL URL
DATABASE_SSL_REQUIRE=True
WHATSAPP_PHONE_NUMBER=917440977161
AUTO_SEED_CATALOG=True
```

Custom domain lagane ke baad:

```text
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

## Important

Uploaded product images local `media/` folder me hain. Real launch ke liye media files ko cloud storage ya Render persistent disk par shift karna hoga, warna redeploy ke baad new uploaded files ja sakti hain.

Initial launch ke liye `AUTO_SEED_CATALOG=True` production database me GarlicShop catalog products aur galleries create karega. Real customer uploads/live admin images ke liye later cloud storage add karein.
