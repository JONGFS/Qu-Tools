# Handoff Release Checklist

## API and cache

- [x] Credentials load from an ignored `.env`
- [x] OAuth client-credentials authentication returns a token
- [x] Menu requests include location/channel/type context
- [x] `X-Generation-Time` is saved
- [x] `PrevGenerationTime` avoids unnecessary downloads
- [x] Empty/204/304 responses safely reuse the complete cache
- [x] Cache entries are isolated by context
- [x] Menu and metadata writes are atomic

## PLU validation

- [x] Aloha PLUs remain identifiers/strings
- [x] A unique exact PLU is authoritative
- [x] A stale derived QU item ID is safely updated
- [x] Multiple item IDs for one PLU require review
- [x] Multiple paths for one item ID remain visible
- [x] Default audit mode skips rows not marked migrated
- [x] The source workbook is never overwritten

## Parser and outputs

- [x] Nested menu children are flattened
- [x] Ancestors and duplicate paths are retained
- [x] Active/deleted and combo/regular states are exported
- [x] Flattened CSV and JSON are generated
- [x] All-result and unsafe-review CSV reports are generated
- [x] Run manifests tie outputs to one menu snapshot and workbook

## Operator handoff

- [x] Location profiles require no Python edits
- [x] One `run` command refreshes, validates, parses, and bundles
- [x] `--help` does not contact QU
- [x] Offline cache inspection is supported
- [x] Setup, operations, status, architecture, and troubleshooting docs exist
- [x] Tests cover the supported workflow

## Deliberately deferred

- [ ] Direct EI database/API validation
- [ ] Multi-context availability matrix
- [ ] Order Simulator `items_config` generation and installation
- [ ] Web UI and scheduled monitoring
