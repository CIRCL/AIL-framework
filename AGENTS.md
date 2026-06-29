# AGENTS.md

## Repository purpose

This repository contains the AIL Framework, a Python-based platform for collecting, crawling, processing, enriching, searching, correlating, and exporting unstructured intelligence data from clear-web sources, Tor/I2P services, chats, files, and external feeds.

## High-level architecture

AIL is organized around an ingestion-to-analysis pipeline:

1. **Collection and import** bring external data into the framework.
2. **Core queues and modules** process objects asynchronously.
3. **Object libraries** provide typed access to stored intelligence objects.
4. **Trackers, search, correlation, and investigations** support analysis workflows.
5. **Exporters and integrations** disseminate findings to external systems.
6. **The Flask web UI and API** expose the analyst-facing application.

## Important directories

- `bin/` - Main runtime code and launch/update scripts.
  - `bin/AIL_Init.py` initializes the framework.
  - `bin/LAUNCH.sh` launches AIL components.
  - `bin/Update.py`, `bin/Update-conf.py`, and `bin/update-background.py` support upgrades and background update tasks.
- `bin/core/` - Core synchronization, screen/process helpers, and AIL-to-AIL components.
- `bin/importer/` - Import pipelines that ingest data into AIL.
  - `bin/importer/feeders/` contains source-specific feeder parsers for chats, crawlers, URLs, and other external inputs.
- `bin/crawlers/` - Crawler runtime code, including website/forum crawler components.
- `bin/modules/` - Processing and analysis modules. Modules subscribe to queues and extract, enrich, tag, index, or alert on AIL objects.
  - `bin/modules/TemplateModule.py` is the starting point for new modules.
  - `bin/modules/abstract_module.py` contains shared module behavior.
- `bin/lib/` - Shared application libraries for configuration, queues, users, tags, trackers, search, correlation, crawlers, statistics, updates, and other framework services.
  - `bin/lib/objects/` defines typed object abstractions such as items, domains, messages, screenshots, images, CVEs, usernames, mails, QR codes, PDFs, and correlation-related objects.
- `bin/exporter/` - Export integrations such as MISP, TheHive, mail, and webhooks.
- `bin/trackers/` - Runtime tracker and retro-hunt implementations for terms, regexes, typo-squatting, and YARA.
  - `bin/trackers/yara/` contains bundled and custom YARA rule locations.
- `var/www/` - Web application code and assets.
  - `var/www/blueprints/` contains Flask blueprints/routes.
  - `var/www/templates/` contains Jinja templates grouped by feature area.
  - `var/www/static/` contains CSS, JavaScript, images, and other browser assets.
- `configs/` - Runtime configuration samples and defaults.
  - `configs/modules.cfg` controls which modules are enabled and how they are wired to queues.
  - `configs/core.cfg.sample` and `configs/update.cfg.sample` are sample configuration files.
  - `configs/docker/`, `configs/keys/`, and related subdirectories contain environment-specific configuration material.
- `files/` - Static dictionaries, word lists, protocol/TLD files, and external taxonomy/galaxy data used by modules and tagging logic.
- `tools/` - Operator and maintenance utilities such as import helpers, user creation, reindexing, reprocessing, and crawler task submission.
- `tests/` - Pytest-based regression and API/module tests.
- `doc/` - Project documentation, API notes, screenshots, and architecture diagrams.
- `samples/` - Sample input data.
- `update/` - Versioned update and migration scripts.
- `other_installers/` - Alternative installation assets for platforms such as Docker, LXD, Ansible, and CentOS.
- `logs/` and `var/` - Runtime data directories. Avoid committing generated runtime data unless it is intentionally tracked.

## Data and control flow

- Importers and feeders normalize external data and submit it to AIL.
- Queue configuration in `configs/modules.cfg` determines which modules consume which object types.
- Modules in `bin/modules/` perform extraction, enrichment, indexing, tagging, notifications, and object creation.
- Shared libraries in `bin/lib/` and typed objects in `bin/lib/objects/` should be used instead of duplicating storage, tagging, correlation, queue, or configuration logic.
- The web UI in `var/www/` reads from the same library/object layer and should keep business logic in `bin/lib/` where practical.
- Exporters in `bin/exporter/` should encapsulate outbound integrations and avoid leaking integration-specific details into modules or UI routes.

## Development guidelines

- Prefer adding reusable framework logic under `bin/lib/` and thin feature-specific orchestration in modules, importers, exporters, or Flask blueprints.
- When adding a new processing module:
  1. Add or update the module implementation under `bin/modules/`.
  2. Register the module and its queue subscriptions in `configs/modules.cfg`.
  3. Use `bin/modules/TemplateModule.py` and `bin/modules/abstract_module.py` as references.
- When adding a new object type, follow the patterns in `bin/lib/objects/` and update related UI templates, search/correlation code, and tests as needed.
- When adding web UI features, keep routes in `var/www/blueprints/`, templates in `var/www/templates/`, and static assets in `var/www/static/`.
- When changing configuration behavior, update the relevant sample files in `configs/` and document any migration or update step in `update/` if existing deployments need it.
- Do not commit secrets, API keys, private crawler credentials, generated logs, or local runtime database/cache content.
- Keep imports straightforward; do not wrap imports in broad `try`/`catch` or `try`/`except` blocks.
