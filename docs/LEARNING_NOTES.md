# Learning notes

## CH05: database model and startup (state at that checkpoint)

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

## CH06: persisted site CRUD

- HTTP site CRUD now uses PostgreSQL and UUID route ids. The Chapter 4 in-memory
  module has been removed; this supersedes CH05's temporary storage limitation.
- Request -> `Depends(get_session)` -> `SiteService` -> PostgreSQL -> `SiteRead`.
  FastAPI validates UUIDs and input bodies before calling the service. A malformed
  UUID/body is 422; a valid UUID with no record is 404.
- This project retains SQLAlchemy `AsyncSession`, so reads use
  `await session.execute(select(Site))` and then `scalars().all()` or `first()`.
  Bookly uses SQLModel `AsyncSession.exec()` instead; the two APIs differ.
- List filtering uses `WHERE Site.active = ...` in SQL. `active=false` is distinct
  from omitting the filter. Routes delegate database work to the service.
- Create adds a Site, commits and refreshes it. Update changes only `active`,
  commits and refreshes. Delete awaits `session.delete` and commits. Failed
  writes roll back and propagate the error; missing records return None so the
  route can return 404. Successful create/delete retain 201/204 status codes.
- Returning `SiteRead` keeps responses limited to the public schema. Committed
  records survive API restarts because storage belongs to PostgreSQL, not Python.

## CH09: JWT authentication

- Login checks the normalized email and stored Argon2 password hash. Both wrong
  password and unknown account return the same generic 401 message. Successful
  login returns a 15-minute access token and a two-day refresh token by default.
- JWTs are signed, not encrypted. Payloads contain user UUID (`sub`), expiry
  (`exp`), unique token id (`jti`) and `token_type`, never passwords/hashes.
  Decode requires all four claims, UUID identities, expiry and the allowed HS256
  algorithm. The signing secret lives only in ignored .env, not source control.
- All /api/v1/sites operations require an access bearer token. Missing, expired,
  tampered, revoked or wrong-type credentials return 401. Health and signup/login
  stay public; the earlier practice endpoints are not authentication mechanisms.
- POST /api/v1/auth/refresh accepts only a refresh bearer token and checks that
  its user still exists before returning a fresh access token. No active flag
  has been added; role/verification enforcement belongs to later checkpoints.
- POST /api/v1/auth/logout accepts an access or refresh bearer token and revokes
  only the presented token. Redis stores careready:revoked:<jti> until that JWT
  expires. Revoking one access token does not revoke its refresh token or other
  devices. Full session-family logout and refresh rotation are not implemented.
- Validation reuses app.state.redis. Redis outages return generic 503 on
  protected requests, refresh and logout (fail closed). Login/signup may still
  succeed, but issued tokens cannot access protected routes during the outage.

## CH10: authentication and authorization

Authentication validates the token and identifies a live account. Authorization checks its current database role against the route policy. The JWT does not grant a permanent role: promotion or deactivation takes effect on the next request. Coordinators can read sites; admins can also change them. Signup never accepts a privileged role.

## CH11: relationships

A foreign key connects a site to its creator and each note to its site and author. A relationship exposes those links to Python; small response schemas control what HTTP reveals. The site/tag link table represents many-to-many membership and its composite key prevents duplicate membership. Async reads must load related data while the session is available.

## CH12: domain errors

The service raises SiteNotFound to describe the failure. A central handler translates it into an HTTP 404 with a stable code and message. Input validation and authentication keep their own error behavior. Clients should branch on codes rather than parsing prose; responses must not contain tracebacks or credentials.
