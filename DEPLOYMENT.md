# Vercel deployment

This project uses Vercel's Python runtime and requires a hosted PostgreSQL database in production. Do not use the committed `db.sqlite3` database on Vercel: serverless filesystems are not persistent.

## Vercel project settings

Set these environment variables for **Production**, **Preview**, and **Development** as appropriate:

- `DJANGO_SECRET_KEY`: a long random value, for example from `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DATABASE_URL`: the connection string from Neon, Supabase, or another managed PostgreSQL provider
- `DJANGO_ALLOWED_HOSTS`: your custom domain, without `https://` (the default `*.vercel.app` host is already allowed)
- `DJANGO_CSRF_TRUSTED_ORIGINS`: your full HTTPS origin, such as `https://booking.example.com`
- `DJANGO_DEBUG`: `False`

Deploy from the repository root. Vercel runs `build.sh`, which collects static files, and `api/index.py` serves the Django WSGI application.

## Initialize the production database

Run migrations against the hosted database before the first client visit. Replace the example URL with the real connection string from your provider; do not copy the words `user`, `password`, `host`, or `database` literally:

```bash
DATABASE_URL="postgresql://..." python manage.py migrate
DATABASE_URL="postgresql://..." python manage.py createsuperuser
```

To move the existing local users and booking data, export it before migrating and load it into the hosted database after migrations:

```bash
python manage.py dumpdata --natural-foreign --natural-primary -o data.json
DATABASE_URL="postgresql://..." python manage.py loaddata data.json
```