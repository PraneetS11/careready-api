# Care network increment

CareReady now supports requester, provider and agency accounts through `/api/v1/network/register`. Existing chapter endpoints remain compatible. All operational routes require verified email. An agency approves only its own verified providers; approval represents the agency's manual review, not automated credential verification.

Requesters submit one-time or weekly visits (1–12 occurrences). An agency publishes its own requests. Providers see only open, future visits for their agency, service types and experience level, excluding schedule conflicts with a 30-minute travel buffer. Acceptance locks the provider and visit records to prevent duplicate and overlapping assignments. City centroids appear on the public job view; recipient, address, notes and requester identity are withheld until assignment. Agency and requester views are ownership-scoped.

Gender, language, communication style, smoke-free preferences and pets are fit information, not automatic employment exclusions. Experience is four simple levels. Providers declare services/languages; agencies must review suitability before approval. Recurrence preserves the local city timezone across daylight saving and rejects nonexistent local times. Each occurrence is a separate visit and is cancelled independently.

Agency equipment inventory records asset codes and available/in-use/maintenance states. Equipment reservation, payments, clinical charting, formal credential validation, recurring-series editing and automatic dispatch are not implemented. This is a local fictional-data demonstration.

Verification: `make lint`; `RUN_INTEGRATION=1 make test` (65 passing); `.venv/bin/python scripts/verify_network.py` against `compose.test.yaml` confirms isolation, preferences, recurrence, privacy, acceptance races and equipment ownership. The latter runs in CI too.
