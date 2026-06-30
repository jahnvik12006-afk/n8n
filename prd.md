# Product Requirements Document — AutoAnimeBot

**Version:** 2.0
**Status:** Draft
**Owner:** Pihu

---

## 1. Overview

AutoAnimeBot is a production-grade Telegram bot for automating anime content posting and distribution. It searches anime via an external API, lets admins select episodes/languages, downloads and uploads content to Telegram channels, and posts promotional cards to a main channel.

This document treats the bot as a **backend service with a Telegram transport layer**, not a script. The previous draft described folder structure and flows but not *why* it would be fast — this version fixes that by specifying the actual low-level mechanisms that determine response latency: webhook vs polling, connection pooling, worker concurrency, caching layers, and message rendering, including the font/monospace requirement.

## 2. Why the Previous Design Would Be Slow (Root Causes)

Before specifying the fix, naming the actual bottlenecks a naive implementation hits:

1. **Long polling instead of webhooks** — `getUpdates` long polling adds inherent latency (200ms–1s+ per cycle) vs webhooks which push updates instantly.
2. **New HTTP client per request** — creating a fresh `aiohttp.ClientSession` or Mongo connection per call instead of a long-lived pooled client adds 50–200ms of TCP/TLS handshake overhead every single time.
3. **One worker doing everything** — if search, download, and upload all run on the same single async task with no worker pool, one slow download blocks all other user interactions even though the code is "async".
4. **Uncached repeated API calls** — re-querying the anime API for metadata Telegram already showed 10 seconds ago instead of serving from cache.
5. **No connection reuse to Telegram's Bot API** — not setting a shared `aiohttp` session with keep-alive for outgoing `sendMessage`/`editMessageText` calls.
6. **Blocking file I/O inside async functions** — using `open()`/`requests` instead of `aiofiles`/`httpx.AsyncClient` anywhere in the download/upload path silently blocks the entire event loop.
7. **No backpressure on the job queue** — unlimited concurrent downloads/uploads competing for bandwidth and Telegram flood limits, causing everything to slow down together instead of failing gracefully.

Section 14 below converts each of these into an explicit, testable requirement.

## 3. Goals

- Sub-300ms perceived response time for any inline button press or command (button press → message edit acknowledgement)
- Fully async architecture, zero blocking operations anywhere in the hot path
- Reliable retry mechanism at every external call boundary
- Resume-safe job queue (survives bot restarts)
- Clean, modular, extensible codebase (handlers / services / models / ui separated)
- Admin-only control surface
- Consistent HTML-based, no-emoji, symbol-driven UI with **monospace font styling** (cyan/white/gray theme)
- Centralized logging and error tracking in MongoDB

## 4. Non-Goals

- No public/non-admin posting access
- No emoji-based UI elements
- No synchronous/blocking code paths
- No multi-bot/multi-tenant support (single bot instance, single MongoDB)

## 5. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Bot framework | Telegram Bot API, **webhook mode** | Not long polling — see §6 |
| HTTP client | `httpx.AsyncClient` (single shared instance) | Connection pooling + HTTP/2 |
| Database | MongoDB via `motor` | Indexed collections, see §11 |
| In-memory cache | `cachetools.TTLCache` or `asyncio`-safe LRU | Hot-path cache in front of Mongo |
| Event loop | `uvloop` | Installed as default loop policy |
| Async runtime | `asyncio` | Worker-pool pattern, see §10 |
| Web server (webhook receiver) | `aiohttp.web` or `FastAPI` + `uvicorn` | Receives Telegram updates |

## 6. Transport: Webhook, Not Long Polling

**Requirement:** the bot MUST run in webhook mode in production, not `getUpdates` polling.

- A lightweight `aiohttp.web`/FastAPI server receives `POST` updates from Telegram on a registered HTTPS endpoint
- Update is parsed and immediately handed to the dispatcher as a fire-and-forget `asyncio.create_task()` — the webhook handler returns `200 OK` to Telegram *before* business logic finishes, so Telegram never waits on the bot's processing time
- This alone removes the single biggest source of perceived "bot is slow" complaints

## 7. Folder Structure

```
Root/
├── main.py                 # entrypoint: sets uvloop policy, starts webhook server
├── .env
├── requirements.txt
│
├── core/
│   ├── bot.py               # singleton Bot instance
│   ├── config.py
│   ├── database.py          # motor client singleton + index setup
│   ├── http_client.py       # shared httpx.AsyncClient singleton (connection pool)
│   ├── logger.py
│   ├── cache.py             # in-memory TTL cache layer in front of Mongo
│   ├── retry.py             # retry decorator with exponential backoff
│   ├── scheduler.py
│   ├── webhook_server.py    # aiohttp/FastAPI receiver
│   ├── worker_pool.py       # bounded worker pool for downloads/uploads
│   ├── downloader.py
│   ├── uploader.py
│   ├── api.py
│   └── utils.py
│
├── handlers/        # start, admin, search, slug, upload, channels, callback, errors, jobs
├── ui/               # theme, cards, buttons, dialogs, templates, html builder
├── services/         # api_client, metadata, telegram_upload, post_creator, search
├── models/           # anime, episode, job, user
├── middlewares/       # admin-only gate, cooldown, logging
└── temp/              # transient download storage (cleared on a timer)
```

**Design principle:** handlers stay thin — parse input, enqueue work or call a cached service, acknowledge immediately. Anything slow (download, upload, external API) goes through the worker pool, never inline in the handler that's responding to the user.

## 8. Configuration (.env)

| Key | Purpose |
|---|---|
| `BOT_TOKEN` | Telegram bot token |
| `BOT_START_IMAGE` | Start command banner image |
| `WEBHOOK_URL` | Public HTTPS URL Telegram pushes updates to |
| `WEBHOOK_SECRET` | Secret token to validate incoming webhook requests |
| `MONGODB_URL` | Mongo connection string |
| `API_BASE` | Anime metadata/source API base URL |
| `DOWNLOAD_DELETE_TIMER` | Seconds before temp files are purged (840s default) |
| `MAIN_CHANNEL` | Main promo channel ID |
| `ADMINS` | Comma-separated admin user IDs |
| `LOG_LEVEL` | Logging verbosity |
| `MAX_RETRY` | Max retry attempts per stage |
| `REQUEST_TIMEOUT` | HTTP timeout in seconds |
| `MAX_CONCURRENT_UPLOADS` | Worker pool size for upload pipeline (default 2–3, see §10) |
| `HTTP_POOL_SIZE` | Max connections in the shared httpx pool |
| `CACHE_TTL_SECONDS` | Default in-memory cache TTL |

## 9. UI Requirements (incl. Font)

- All messages are HTML-formatted (`parse_mode=HTML`)
- No emojis anywhere
- Allowed symbol set only: `│ ├ └ ■ □ • ◆ ◇ ▲ ▼ ▶ ◀ ╭ ╰`
- **Font requirement:** all structured/data blocks (titles, key-value pairs, episode lists, IDs, job status) are wrapped in `<code>` or `<pre>` tags to render in **monospace font** — this is what makes the symbol-box layout (`│ ├ └`) actually line up visually instead of looking broken on variable-width font. Plain conversational lines (e.g. "Choose action below.") stay outside `<code>` in normal font for readability contrast.
- Theme: cyan/white/gray conveyed via `<b>` (bold) for headers and `<code>` (monospace, slightly greyed in Telegram's renderer) for data — Telegram HTML doesn't support arbitrary text color, so theme is expressed through bold/monospace/spacing discipline, not actual color codes
- All actions use inline keyboards — no reply keyboards, no emoji buttons
- Example card with font tags applied:

```html
╭────────────────
<b>AutoAnimeBot</b>

<pre>Title     : Solo Leveling
Language  : Dual Audio
Episodes  : 24
Status    : Ongoing
Season    : 2</pre>
────────────────
Choose action below.
╰────────────────
```

## 10. Concurrency Model — Worker Pool (Core Fix for Slowness)

This is the part the original design was missing.

- A **bounded async worker pool** (`asyncio.Semaphore` or a fixed set of consumer tasks reading from an `asyncio.Queue`) handles all downloads/uploads
- Pool size controlled by `MAX_CONCURRENT_UPLOADS` (default 2–3, tuned to avoid Telegram flood limits on a single bot)
- **Handlers never await a download/upload directly.** A handler enqueues a `Job` document, fires an immediate "Queued" acknowledgement message back to the admin, and returns. The worker pool consumes the queue independently.
- This guarantees: no matter how many downloads are in progress, a `/stats` or search command from the admin still responds in milliseconds, because it's handled on a separate, unblocked code path
- Within one episode-range batch, uploads to channels stay **sequential per job** (per original requirement, to respect Telegram per-chat flood limits) but **different jobs can run concurrently** up to the pool size

## 11. Caching Strategy (Two-Tier)

**Tier 1 — In-memory TTL cache** (`core/cache.py`): sits in front of everything, checked first. Sub-millisecond reads. Used for search results and metadata that was just fetched in the last `CACHE_TTL_SECONDS`.

**Tier 2 — MongoDB cache collection**: durable, survives restarts, longer TTL via Mongo's native TTL index (`expireAfterSeconds`). Checked on Tier-1 miss before hitting the external API.

Cached entities: search results, anime metadata, episode lists, image URLs, channel mappings.

**Indexing requirement:** every Mongo collection used in the hot path (`cache`, `jobs`, `users`) must have explicit indexes on lookup fields (`slug`, `job_id`, `telegram_id`) — unindexed queries are a silent latency killer at scale even on async drivers.

## 12. Core User Flows

### 12.1 Search Flow
1. Admin sends an anime name (e.g. "Solo Leveling")
2. Cache checked (Tier 1 → Tier 2) before any API call
3. On miss: bot queries the API (`services/search.py`), result cached on the way back
4. Bot renders a result card (monospace data block per §9): cover image, title, slug, language, episodes, season, quality, status, genres, duration, last updated
5. Inline button: `View Episodes`

### 12.2 Slug / Episode Flow
1. Admin runs `/post <slug>`
2. Episode list resolved via cache-first lookup
3. Bot shows language selector: Hindi / English / Japanese / Dual Audio
4. On language selection, bot shows upload-mode dialog: **Single Upload** or **Multiple Upload**

### 12.3 Multiple Upload Flow
1. Bot asks for **Start Episode** → admin replies
2. Bot asks for **End Episode** → admin replies
3. Bot asks for **Upload Channel** via inline keyboard: Main Sub / Hindi / English / Dual / Movies / Anime
4. Bot immediately responds "Job Queued" and hands off to the worker pool — admin is not blocked waiting for the batch to finish

### 12.4 Upload Pipeline (per episode, inside a worker)
1. Resolve download URL via API (cached where possible)
2. Download file via shared `httpx.AsyncClient` (with retry)
3. Upload to target Telegram channel (with retry)
4. Delete temp file
5. Move to next episode in the batch — sequential within the job, concurrent across jobs

### 12.5 Main Channel Promo Flow
1. Admin chooses **Post Before Download**
2. Bot posts a promo card to `MAIN_CHANNEL`
3. Inline button: `DOWNLOAD NOW` → redirects to the relevant sub-channel

## 13. Retry System

Applies to every external-call stage: API calls, downloads, uploads, Mongo writes, Telegram calls.

- Max attempts: 3 (configurable via `MAX_RETRY`)
- Backoff: exponential — 2s → 5s → 10s, with jitter to avoid thundering-herd retries when multiple jobs fail at once
- On final failure: job marked `Failed`, error logged with full context to MongoDB
- Retry logic implemented once as a reusable decorator (`core/retry.py`), applied consistently — not copy-pasted per call site

## 14. Performance Requirements (Explicit, Testable)

| Requirement | Mechanism |
|---|---|
| Telegram updates received with near-zero added latency | Webhook mode, not polling (§6) |
| Button press acknowledged in <300ms | Handler never awaits slow work inline; worker pool handles it async (§10) |
| No per-call connection setup cost | Single shared `httpx.AsyncClient` and single `motor` client, both long-lived singletons (§5, §7) |
| Repeated lookups don't re-hit the API | Two-tier cache, checked before any network call (§11) |
| One slow download never blocks other commands | Bounded worker pool + `asyncio.Queue`, isolated from handler dispatch (§10) |
| No silent event-loop blocking | All file I/O via `aiofiles`, all HTTP via async clients — zero use of `requests`, `open()`, or `time.sleep()` anywhere in async code |
| Mongo queries stay fast under load | Explicit indexes on all hot-path lookup fields (§11) |
| Bot doesn't trip Telegram flood limits | `MAX_CONCURRENT_UPLOADS` cap + sequential-per-job upload order |

## 15. Job Queue & State Management

Each upload is tracked as a unique **Job**:

`Pending → Downloading → Uploading → Completed`
(or `Failed` / `Cancelled` at any stage)

- Jobs persist in MongoDB so the queue **survives bot restarts** — on startup, any job left in `Downloading`/`Uploading` state is requeued
- `/jobs` admin command surfaces current queue state, pulled from cache-fronted Mongo read, not a blocking full collection scan

## 16. Admin Commands

| Command | Purpose |
|---|---|
| `/admin` | Admin panel |
| `/stats` | Bot/usage statistics |
| `/logs` | View recent logs |
| `/setmain` | Set main promo channel |
| `/addsub` | Add a sub-channel |
| `/removesub` | Remove a sub-channel |
| `/listsub` | List configured sub-channels |
| `/reload` | Reload config/cache |
| `/cache` | Cache management (inspect/clear Tier 1 + Tier 2) |
| `/jobs` | View job queue |
| `/broadcast` | Broadcast a message |
| `/cancel` | Cancel an active job |

Gated by `middlewares/admin.py` — non-admins get no functional access.

## 17. Error Handling & Logging

- Global exception middleware catches all unhandled errors
- Each error record in MongoDB: Job ID, stack trace, API endpoint, request duration, retry count
- Every request logged: timestamp, user, endpoint, latency, retry count, success/failure
- `LOG_LEVEL` controls verbosity

## 18. Data Models

| Model | Key Fields (conceptual) |
|---|---|
| `Anime` | slug, title, cover, genres, status, season, languages |
| `Episode` | anime_slug, number, quality, download_url, language |
| `Job` | job_id, type, status, retry_count, created_at, updated_at, payload |
| `User` | telegram_id, is_admin, cooldown_until |

## 19. Open Questions / Future Extensions

- Should completed jobs auto-purge from Mongo after N days, or persist indefinitely for audit?
- What's the right `MAX_CONCURRENT_UPLOADS` ceiling before Telegram starts flood-limiting the bot account — needs empirical tuning per channel tier?
- Any plan for a web dashboard on top of the same MongoDB job/log data?
- Multi-API-source failover (similar to Hiotaku's provider strategy pattern) — in scope for v1 or later?
- Horizontal scaling: if load grows, does the worker pool move to a separate process/machine consuming the same Mongo job queue?

## 20. Success Criteria

- Admin can search → select → upload a full episode range to a channel with zero manual file handling
- Any command/button responds in under 300ms regardless of how many downloads/uploads are active in the background
- A killed/restarted bot resumes pending jobs without data loss or duplicate uploads
- No blocking calls detectable under load (verified via async profiling / event-loop lag monitoring)
- All UI messages render correctly with no emoji, monospace-aligned data blocks, and consistent symbol-based framing
