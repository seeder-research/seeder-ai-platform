# AI Platform — Phase 1

Foundation layer: cluster networking/Docker topology, PostgreSQL schema, FastAPI
backend with LDAP auth and connector-based external model routing, and a Next.js
frontend skeleton. Bose01's inference server (LiteLLM + SGLang) is deployed
separately — everything here treats it as an external dependency reachable at
`LITELLM_URL`, speaking the OpenAI-compatible API.

## Directory structure

```
docker-compose/   Per-node Docker Compose files + Traefik/Keepalived configs
database/         schema.sql — authoritative Phase 1 Postgres schema
backend/          FastAPI app (auth, admin, connectors, chats, models, WS streaming)
frontend/         Next.js app (login, single chat, model/connector selector)
```

## Smoke test plan (deferred until you're ready)

1. **Database**: apply `database/schema.sql` to a running PostgreSQL instance
   (`psql -d aiplatform -f database/schema.sql`). This is the authoritative
   schema for Phase 1 — Alembic is scaffolded under `backend/alembic` for
   tracking future changes, but isn't required to bootstrap this baseline.

2. **Backend**: copy `backend/.env.template` to `backend/.env` and fill in real
   values — particularly `LDAP_*` (pointed at Feynman; LDAP auth uses StartTLS,
   validated against the system trust store by default, so no extra config is
   needed if the server cert in `/usr/local/share/ca-certificates` has already
   been registered via `update-ca-certificates`), `BOOTSTRAP_ADMIN_UID` (your
   own LDAP uid, so you become admin on first login), and
   `CONNECTOR_ENCRYPTION_KEY` (generate via
   `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).
   `LITELLM_URL`/`LITELLM_MASTER_KEY` need a reachable LiteLLM instance — auth
   and connector management work without one, but sending an actual chat
   message does not.

3. **Frontend**: `npm install` inside `frontend/`, then `npm run dev`. Confirm
   the middleware redirects an unauthenticated visit to `/login`, log in with
   real LDAP credentials, and confirm redirect to `/chat`.

4. **Connectors**: visit `/connectors` in the frontend — confirm the 4 seeded
   rows (OpenAI, Anthropic, Google Gemini, OpenRouter) appear with
   `is_configured: false`, set an API key on one, confirm `is_configured`
   flips to `true` and identity fields remain locked.

5. **Chat**: with a connector key configured and a reachable LiteLLM instance,
   select that connector in the chat page, type the underlying model name
   (e.g. `gpt-4o`, `claude-opus-4-1`, `gemini-2.5-pro`), and confirm streaming
   tokens render correctly.

## Known deferred items

- Bose01 SGLang/LiteLLM deployment itself (separate workstream)
- Tool/function calling — explicitly deferred to Phase 3 (Orchestrator/Agent/Reviewer)
- FLUX.2-Klein and Fish Audio S2 Pro inference servers — deferred, GPU 7 on
  Bose01 reserved for them
- Guardrails container is currently a placeholder image
  (`ai-platform/guardrails:latest`) — not yet implemented

## Node substitution note

Redis + WireGuard were originally assigned to Schrodinger03; that node is currently
down, so this package runs them on **Dirac02** instead — same
hardware class, no conflicting role. See `docker-compose/dirac02/`.

## Sanitization notes (for GitHub publishing)

No real IP addresses appear anywhere in this repository. They're handled in
three different ways depending on what actually consumes the file:

**1. Docker Compose files** (`docker-compose/{schrodinger01,schrodinger02,
feynman,bose01,dirac02}/docker-compose.yml`) use `${NODE_IP}`-style variables
— e.g. `${SCHRODINGER01_IP}`, `${FEYNMAN_IP}` — substituted by the `docker
compose` CLI from the `.env` file in that same directory. This matters because
Docker's `ports:` host-IP binding and WireGuard's `PEERDNS` both require a
**literal IP** (no hostname resolution at all), so the real IP has to land
there at compose-up time. Each `.env.template` lists the variables it needs
with a `<replace-with-actual-ip>` placeholder — copy it to `.env` (gitignored)
and fill in real values before deploying.

**2. LiteLLM's `bose01/litellm/config.yml`** isn't a Compose file (LiteLLM
reads it directly inside its own container), so the `${VAR}` mechanism above
doesn't apply to it. Instead, it references the SGLang containers by their
**Docker Compose service names** (`sglang-qwen3.6-27b`, `sglang-gemma4-31b-it`)
rather than any hostname or IP — since they're services in the same Compose
project, Docker's built-in network DNS resolves these automatically, with no
configuration needed at all.

**3. Keepalived configs and Traefik's `dynamic/services.yml`** are the only
files that still need manual editing before deploying. Neither is processed
by `docker compose` (Keepalived runs as a system service; Traefik's dynamic
config is a static file it reads from disk), so there's no substitution
mechanism available — each has an inline comment marking exactly what to
replace. Keepalived's `virtual_ipaddress` is a hard requirement (literal
IP/CIDR only); Traefik's backend URLs are cosmetic (they resolve fine as
hostnames if you have DNS or `/etc/hosts` entries for `schrodinger01` /
`schrodinger02`, otherwise replace with real IPs).

A `.gitignore` is included to keep real `.env` files (which contain secrets
and IPs) out of version control — only the `.env.template` files should ever
be committed.
