# Free-tier deployment

The repository is configured for a Render Blueprint that hosts the static web client and FastAPI service, with Neon Free as the PostgreSQL provider. This keeps the database on a persistent managed Postgres service instead of Render Free Postgres, which expires after 30 days.

## Deploy

1. Create a Neon Free project and database. In Neon, open **Connect**, select the database role and branch, and copy the pooled connection string. Keep the connection string private; it contains the database password.
2. Push this repository to a Git provider connected to Render.
3. In Render, create a **Blueprint** from the repository and select `render.yaml`.
4. When prompted for `DATABASE_URL`, paste the Neon connection string. The app and Alembic normalize Neon’s `postgresql://` URL for the installed psycopg 3 driver.
5. Deploy both services. The web build receives the API URL from Render. Check the API at `https://contridedo-api.onrender.com/health` and the web app at `https://contridedo-web.onrender.com`.
6. If Render assigns a different static-site URL, update the API service's `CORS_ORIGINS` value to that exact origin and redeploy the API.

Render Free web services sleep after 15 minutes without traffic and can take about a minute to wake. Their filesystems are ephemeral, so do not use SQLite for hosted data. Render's free Postgres expires after 30 days, which is why this setup uses Neon instead. Neon Free currently includes 1 GB of Postgres storage per project, 100 compute-hours per project, and 5 GB of network egress; compute scales to zero after five minutes idle. Free tiers can change, and this is appropriate for a hobby deployment, not production financial records or data that needs backups/SLA guarantees.

## Android

After the API has its Render URL, build an APK pointed at it with:

```powershell
Set-Location android
.\gradlew.bat assembleDebug -PapiBaseUrl=https://contridedo-api.onrender.com/
```

The default URL remains the Android emulator's local backend address for development.

## Local database URL

Set `DATABASE_URL` to a local PostgreSQL URL and run migrations with `alembic upgrade head` from `backend/`. The hosted service runs this migration command on startup because Render's pre-deploy command is not available on the Free web plan.