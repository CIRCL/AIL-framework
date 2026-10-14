# Geolocation storage configuration

Phase 1 introduces the dedicated GEO storage engine. Update configuration before using its methods on an existing AIL installation:

```bash
python bin/Update-conf.py
```

Run this from the AIL repository with the usual AIL environment variables and virtual environment. The existing updater adds the `[Kvrocks_GEO]` section from `configs/core.cfg.sample` and preserves existing configuration values. Its default connection uses port 6383 and the GEO namespace token already defined by `namespace.geo` in `configs/6383.conf`. Adjust the connection to match the installation's actual namespace token and server address.

For installations whose active Kvrocks configuration predates the GEO namespace, add that namespace through the deployment's normal Kvrocks configuration process. Adding the Python connection section alone does not create a server namespace. Verify that authenticating through `Kvrocks_GEO` reaches the intended namespace before using the engine; do not point it at the objects or default database.

The new format uses these keys inside the GEO database:

| Key | Structure |
| --- | --- |
| `geo:observation:<geo_id>` | Original coordinates, owner global ID, creation/update timestamps in Unix milliseconds, revision, and optional `created_by`, `updated_by`, and `source`. |
| `geo:object:<obj_gid>` | Location IDs ordered by creation timestamp. |
| `geo:index:all` | Spatial index of every location ID. |
| `geo:index:type:<obj_type>` | Spatial index of location IDs for an object type. |

Latitude is automatically clamped to `[-85.05112878, 85.05112878]` for spatial indexing. Records keep the original valid WGS84 coordinates. Confidence/probability fields are absent. Timestamps are metadata and are not the time of the underlying location observation.

The engine connects lazily, so importing the object libraries does not require the new connection section until a GEO operation is performed. Object deletion now performs GEO cleanup and therefore needs this connection even when the object has no locations. Configure the GEO namespace before deploying phase 2 or later. Phases 3 and 4 provide API/session CRUD routes and the Leaflet map UI.

Missing or invalid `[Kvrocks_GEO]` connection settings return a JSON `503` with configuration instructions. Correct the section using `python bin/Update-conf.py` and verify the connection. Failed connection initialization is not cached, so a corrected configuration can be retried without restarting the server. HTML server/proxy errors in the panel show their HTTP status instead of suggesting a login failure; authentication responses are reported separately.

## API and session operations

See [the API documentation](../api.md#object-geolocation) for payloads, responses, and status codes. The API routes are `/api/v1/object/geolocations` and `/api/v1/object/geolocations/<geo_id>`, with the owner's global ID in `gid`. Readers may list/read; users and administrators may create/update/delete. Token endpoints require an API key and reject `user_no_api` users.

The equivalent session routes are `/objects/geolocations` and `/objects/geolocations/<geo_id>`, under the application's configured URL prefix. Session mutations also allow `user_no_api` users and require `X-CSRF-Token`. Fetch `/objects/geolocations/csrf` using the same authenticated session to obtain the token, or use the `geo_csrf_token()` template global. Read-only users cannot mutate locations. The shared UI panel uses these session routes.

Manual creates record the authenticated actor as `created_by` and `updated_by`, and set `source` to `manual`. Changed coordinates update the editor and revision while retaining creation metadata. These fields are server-controlled; client IDs, confidence scores, and provenance overrides are rejected. PATCH requires `expected_revision`; DELETE optionally accepts it. All operations check object existence and observation ownership. JSON bodies are bounded to 4096 bytes.

## Map and location editing

Open **Object locations** on an object's detail page. The shared panel is included on correlation pages (including images and screenshots), items, messages, forum posts, domains, authors, barcodes, OCR, PDFs, QR codes, chats, subchannels, chat threads, and user accounts. Compact image/chat cards link to the dedicated location page at `/objects/geolocations/view?gid=...`; other registered objects can use that page directly. The page validates object existence and read permissions before rendering.

The panel header shows the location count in the initial page HTML, including `0` for objects without locations. Rendering reads only the count; if it cannot be retrieved, the badge shows `?` with an explanatory tooltip and the object page remains usable. Opening the panel loads the first 100 locations and the bundled Leaflet assets. Previous/Next navigate all coordinates, with an explicit range/count; markers show the current page. Initially closed panels do not load coordinates, Leaflet, or map tiles. Compact links display a count only if their metadata already provides `geo_count`, avoiding extra database calls per card.

Users can add decimal latitude/longitude or click the map to fill the fields; clicking alone does not save. Adding a point opens the final page so its coordinates are visible. Editing selects an existing entry and sends its revision. Removal requires confirmation and sends the entry's revision. Conflicting edits refresh the table, preserve entered coordinates, and require selecting the refreshed entry before saving again. Read-only users see coordinates and map controls without mutation controls; server-side permissions remain enforced.

The tile URL is hardcoded to `https://geo.circl.lu/hot/{z}/{x}/{y}.png`. There are no tile-server configuration options. The map's attribution control is disabled, so the Leaflet/OpenStreetMap footer is absent. Previously added `[Geolocation]` tile settings are ignored; no configuration update is needed for the map. The dedicated `[Kvrocks_GEO]` storage connection remains required.

The original polar coordinates remain visible and editable in the table; their markers are drawn at Leaflet's projection limit with an explicit explanation. Tile errors leave markers, tables, and editing usable. If Leaflet JavaScript or CSS cannot load, the table and decimal entry still work. Source strings and coordinate popups use DOM text nodes. Leaflet CSS is shipped with the feature; vector markers avoid dependencies on untracked marker images.

Hover a map point to view its original latitude/longitude and location metadata: source, creation/update timestamps, creator/editor when available, revision, location ID, and owner global ID. Hover tooltips are positioned inside the map, including near polar points. Clicking a point opens the same details and, for users with write access, the edit button. Metadata uses text nodes, so source/actor strings cannot inject HTML into tooltips or popups.

## Object metadata and deletion

Request `options={'geo'}` in an object's `get_meta()` call to include a bounded location summary:

```json
{
    "geo": {
        "locations": [],
        "total": 0,
        "offset": 0,
        "limit": 100,
        "has_more": false
    }
}
```

Each entry in `locations` contains the original coordinates and the observation's ID, owner, timestamps, and revision. The default summary includes at most 100 locations. Use `obj.get_geo_meta(offset=..., limit=...)` for additional pages, up to 1000 entries per page. Request `options={'geo_count'}` for a count without retrieving coordinates. Combining both options reuses the summary's count. Ordinary metadata calls do not query the GEO database.

The common object deletion hook removes GEO records before deleting object metadata. Deletion methods that bypass this hook also explicitly remove GEO records. Several pre-existing deletion methods still have TODOs for files, chat membership, or other object data; phase 2 adds GEO cleanup without implementing those unrelated deletion operations. GEO cleanup errors propagate instead of silently continuing with common metadata deletion.

## Auditing and repairing indexes

With the AIL environment active, perform a read-only audit:

```bash
python tools/repair_geo_indexes.py
```

The tool checks canonical records and their owners, reports missing references, incorrect positions/order, stale references, orphans, and invalid records/key types. The position audit allows the GEO index's coordinate quantization; applying a rebuild always indexes the canonical coordinates again, including latitude clamping.

Pause object and GEO mutations before applying maintenance, since object existence is stored outside the GEO database. Rebuild memberships and spatial indexes, removing stale references:

```bash
python tools/repair_geo_indexes.py --apply
```

To also delete canonical records whose owners no longer exist:

```bash
python tools/repair_geo_indexes.py --apply --remove-orphans
```

Without `--remove-orphans`, orphan observation hashes are retained for review while their invalid memberships/index references are removed. Invalid records and incompatible key types are reported without guessing or overwriting them. Valid observation hashes, IDs, coordinates, creation times, and revisions are preserved. Records and references are repaired in individual watched transactions; the entire maintenance run is not one transaction and can be rerun after interruption.

The JSON report retains at most 100 error details and includes the total error count; reported errors result in exit code 1. The library supports index-only repair without an owner callback, but removing orphan records requires an explicit owner-existence check. The CLI always checks owners using AIL's object library. Repair does not inspect prototype keys or implement migration.

Deletion and geolocation creation span different data stores, and some object deletion implementations are incomplete. Maintenance provides reconciliation for orphan data left by partial operations or concurrent lifecycle changes; it should run with producers paused when cleaning those records.

## Prototype data

The user confirmed that the prototype was not deployed in production. No prototype-data migration or legacy-format compatibility is required. New observations use only the `geo:` format, with no schema version component in their keys. Local experimental data is left untouched.

## Verification

```bash
python -m unittest discover -s tests -p 'test_geo*.py' -v
```

The validation and object-wrapper tests do not require runtime configuration or databases. Integration tests start a temporary Kvrocks process with its own storage directory, Unix socket, and GEO namespace, then stop it and clean up. They never connect to the configured AIL databases. HTTP tests exercise the actual API route functions and session blueprint with Flask clients and isolated Kvrocks; authentication and the object registry are mocked, so they do not start the full AIL server. By default tests use `kvrocks/build/kvrocks`; set `AIL_GEO_TEST_KVROCKS` to another built Kvrocks binary if necessary. When no binary is available, integration tests are explicitly skipped.

`test_geo_ui.py` also runs a real Chromium browser against those routes and a temporary local Flask server. It needs Node and a Chromium binary; set `AIL_GEO_TEST_CHROMIUM` explicitly, or it uses a cached Playwright Chromium headless shell when available. It uses the DevTools protocol directly, without npm or Python browser dependencies. Set `AIL_GEO_TEST_SCREENSHOT` to save an optional PNG from the browser flow. Missing browser prerequisites cause an explicit skip. External tiles are blocked during the test to check offline behavior; authentication, navigation, and the object registry remain fixtures. Full deployment startup and every surrounding detail page are not browser-tested.
