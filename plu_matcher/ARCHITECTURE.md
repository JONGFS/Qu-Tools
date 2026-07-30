# Architecture

QU Tools keeps retrieval, caching, parsing, reconciliation, and reporting
separate while the `run` command coordinates them into one auditable operation.

## Data flow

```text
config/locations.json            .env
  location/context        OAuth client credentials
          \                         /
           \                       /
            ---- location-aware CLI
                       |
                       v
                QU menu endpoint
                       |
          X-Generation-Time / PrevGenerationTime
                       |
                       v
       cache/<location>-<channel>-<type>/
              menu.json + metadata.json
                    /             \
                   /               \
          menu flattening      PLU reconciliation
              |                     |
      CSV/JSON exports       generated workbook/review
                   \               /
                    \             /
             timestamped run bundle
```

## Configuration

`.env` contains only environment and authentication information:

- QU gateway URL
- client ID
- client secret
- integration header value

`config/locations.json` contains non-secret operating profiles:

- profile name
- location ID
- order channel ID
- order type ID
- source workbook path

This separation lets operators change locations without copying credentials or
editing Python.

## Authentication and request boundary

The client uses OAuth 2.0 client credentials. It requests an access token at
runtime and sends the token and integration header on menu requests. Tokens are
not persisted in source control.

The menu request is scoped to exactly one location/channel/order-type profile.
Consequently, the system validates the effective menu response, not the entire
EI database.

## Cache behavior

The context key is:

```text
<locationId>-<orderChannelId>-<orderTypeId>
```

Each context has:

- `menu.json`: the most recently downloaded complete menu;
- `metadata.json`: generation, snapshot, saved, and last-checked evidence.

On refresh:

1. If no complete cache exists, request the full menu.
2. Otherwise send the cached generation time as `PrevGenerationTime`.
3. Save a new menu atomically when QU returns one.
4. If unchanged, update only check metadata.

Saving the menu before its metadata ensures an interrupted first write is
treated as incomplete and safely requested again.

## Menu parser

The API menu is hierarchical. The parser visits every nested child and emits a
record for every item occurrence, retaining:

- item master ID;
- PLU;
- title;
- item and parent path keys;
- item type;
- active/deleted state; and
- ancestor path.

The same item ID can occur on multiple paths, especially inside combos. Indexes
therefore map an ID to a list of nodes rather than one node.

The flattened exports contain these item fields:

```text
item_master_id, plu, title, item_path_key, parent_path_key,
full_path, ancestors, item_type, deleted, active,
path_classification
```

`path_classification` is `REGULAR` or `COMBO`. The CSV repeats provenance
metadata on each row; the JSON groups metadata and item records.

## PLU reconciliation

The Aloha PLU is authoritative for current mapping. The QU item ID in the
workbook is derived evidence.

The reconciler:

1. normalizes the Aloha PLU;
2. indexes active current menu nodes by normalized PLU and item ID;
3. approves one exact PLU that resolves to one unique item ID;
4. updates a stale stored ID when the exact PLU uniquely identifies a new one;
5. preserves all occurrences when that identity has several paths; and
6. blocks automatic selection when a PLU belongs to several item IDs.

The source workbook is read-only. Decisions and audit fields are materialized in
a generated workbook so downstream reads do not depend on Excel recalculating
formulas.

Default audit mode considers migrated rows. `--include-unmigrated` opts into
discovery/reconciliation of other rows and may mark safe mappings as migrated in
the generated workbook.

## Run coordinator and provenance

The `run` command resolves the profile once and uses the same cache/menu
generation for reconciliation and parser exports. It writes a timestamped run
bundle with a manifest tying together:

- tool version and run time;
- location context;
- snapshot and generation time;
- source workbook;
- generated artifacts; and
- safe/review counts.

This prevents the earlier failure mode where a newer menu was interpreted using
an older reconciled workbook.

## Security and data handling

Git ignores:

- `.env` and local profile overrides;
- real API menus and caches;
- company spreadsheets;
- generated runs and reports; and
- logs.

Sanitized fixtures may be committed for deterministic tests. Run bundles can
contain company menu and mapping data and must be shared only through approved
internal channels.

## Non-goals of the current release

The current release does not:

- query all EI configuration;
- automatically choose among multiple item IDs for one PLU;
- prove availability in an unrequested context;
- overwrite the approved source workbook;
- generate or install an Order Simulator `items_config` file; or
- provide a web user interface.

Those are tracked in [FUTURE_WORK.md](FUTURE_WORK.md).
