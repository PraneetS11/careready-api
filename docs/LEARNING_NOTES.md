# Learning notes

## CH05: database model and startup

- **Python app:** the FastAPI process receives HTTP requests and runs Python code.
- **PostgreSQL process:** a separate server stores relational data. The existing
  Compose service exposes PostgreSQL on local port 5434 and Redis on 6382.
- **DATABASE_URL:** connection information: dialect/driver, username, password,
  host, port and database name. Settings reads it from the environment or `.env`.
  It is not the database itself; never copy its password into notes or commits.
- **Engine:** manages database connections and their pool. The existing lifespan
  creates one async engine and shares it with the session factory and `init_db`.
- **Session:** a unit of database work. `get_session` yields a fresh session per
  request and closes it afterward; services own explicit transaction boundaries.
  Sharing one global session would mix concurrent requests' state and transactions.
- **Lifespan:** owns startup and shutdown. It creates the engine, session factory
  and Redis client, initializes tables in development, then serves requests.
  Shutdown closes Redis and disposes the engine; initialization runs inside the
  same cleanup scope so a startup failure also releases those resources.
- **Table versus API schema:** `Site` is a SQLModel database table with a generated
  UUID primary key, name, city, timezone and active flag (default true).
  `SiteCreate` describes input without an id; `SiteRead` includes a UUID id and
  supports reading model attributes. The Chapter 4 `SiteUpdate` remains unchanged.
- **Initialization:** importing `Site` registers it in SQLModel metadata before
  `init_db(engine)` calls `create_all` through an async connection's `run_sync`.
  Existing tables are skipped, so repeated startup does not duplicate them.
  This temporary development-only setup is not a migration system and does not
  alter existing table definitions. Alembic comes later. Test and production
  environments do not automatically create tables.
- **Chapter boundary:** HTTP site CRUD still uses the Chapter 4 in-memory list
  and integer route ids. It does not write to the new UUID table, and its changes
  are lost on process restart. Database-backed CRUD and route UUIDs come in CH06.
