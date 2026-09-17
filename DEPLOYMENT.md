# Vercel deployment

This project uses Vercel's Python runtime and requires a hosted PostgreSQL database in production. Do not use the committed `db.sqlite3` database on Vercel: serverless filesystems are not persistent.

## Create the PostgreSQL database

Create a free PostgreSQL database with a provider such as [Neon](https://neon.tech/), [Supabase](https://supabase.com/), or [Railway](https://railway.app/). Copy its connection string, which normally looks like this:

```text
postgresql://username:password@host/database?sslmode=require&channel_binding=require
```

Do not use the example words in that URL. The project is already configured to use PostgreSQL whenever `DATABASE_URL` is set.

## Vercel project settings

Set these environment variables for **Production**, **Preview**, and **Development** as appropriate:

- `DJANGO_SECRET_KEY`: a long random value, for example from `python -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DATABASE_URL`: the connection string from Neon, Supabase, or another managed PostgreSQL provider
- `DJANGO_ALLOWED_HOSTS`: your custom domain, without `https://` (the default `*.vercel.app` host is already allowed)
- `DJANGO_CSRF_TRUSTED_ORIGINS`: your full HTTPS origin, such as `https://booking.example.com`
- `DJANGO_DEBUG`: `False`

Deploy from the repository root. Vercel runs `build.sh`, which collects static files, and `api/index.py` serves the Django WSGI application.

You can add the database URL with the Vercel CLI, or add it in the Vercel dashboard:

```bash
vercel env add DATABASE_URL production
vercel env add DATABASE_URL preview
vercel env add DATABASE_URL development
```

Repeat this for the other variables listed above, then redeploy:

```bash
vercel --prod
```

## Initialize the production database

Run migrations against the hosted database before the first client visit. Replace the example URL with the real connection string from your provider; do not copy the words `user`, `password`, `host`, or `database` literally:

```bash
DATABASE_URL="postgresql://real-user:real-password@real-host/real-database?sslmode=require" python manage.py migrate
DATABASE_URL="postgresql://real-user:real-password@real-host/real-database?sslmode=require" python manage.py createsuperuser
```

To move the existing local users and booking data, export it before migrating and load it into the hosted database after migrations:

```bash
python manage.py dumpdata --natural-foreign --natural-primary -o data.json
DATABASE_URL="postgresql://..." python manage.py loaddata data.json
```