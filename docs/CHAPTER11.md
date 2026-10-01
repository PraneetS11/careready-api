# CH11: site relationships

Sites have a nullable `created_by_user_id` foreign key and a small creator response containing only ID/email. New site creation uses the authenticated account, ignoring extra client creator fields. Historical sites stay unassigned; backfill only when a verified account-to-site mapping is available.

Coordinators and admins can create/list operational notes at `/api/v1/sites/{site_id}/notes`. Authors come from authentication. Notes contain text, IDs and timestamps; related account hashes are never serialized. Admins create tags at `/api/v1/tags` and attach them at `/api/v1/sites/{site_id}/tags/{tag_id}`. Both roles list site tags. Tags are shared across sites; the link's composite primary key and conflict-safe insert make repeat attachment harmless.

Apply migration `f6e04d091c0c` with the existing Alembic setup. Deleting a site removes its notes and links, preserving shared tags. Deleting a user clears site creator references and removes authored notes. These are fictional development records; retention policy for a future operational audit trail is separate work.

Verified 2026-10-01: 43 tests and full lint pass; migration upgrade/schema comparison pass. Live tests created Hamilton/Toronto sites, attached two notes only to Hamilton, checked authenticated authors and safe creator responses, linked one tag to two sites and two tags to one site, retried attachment, checked missing IDs and coordinator write denial, and restarted the API to verify persistence. Fictional test accounts, sites and tags were removed afterwards.
