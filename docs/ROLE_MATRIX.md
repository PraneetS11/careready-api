# CareReady role matrix (CH10)

| Operation | Coordinator | Admin |
|---|---|---|
| Read sites | Yes | Yes |
| Create, update, delete sites | No (403) | Yes |
| Read own `/api/v1/auth/me` | Yes | Yes |

Signup creates an active coordinator regardless of extra client role fields. Current account and role are loaded from the database for each protected request; disabled/deleted accounts are rejected. This is a global role policy; organization membership is not implemented yet.

Apply migrations with `.venv/bin/alembic upgrade head`. Existing users become active coordinators. Deliberate local administration: `.venv/bin/python -m scripts.promote_admin EMAIL` promotes only the named existing account. Never expose this script as a public endpoint. Login and refresh also reject disabled accounts.

CH11: both roles create/read site notes and read site tags. Admins create tags and attach tags to sites. Note authors and site creators always come from the signed-in account.
