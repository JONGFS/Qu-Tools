# Future Work

These items are deliberately outside the handoff release. Complete operational
adoption of the refresh, PLU check, cache, and parser workflow before expanding
scope.

## Order Simulator configuration refresher

Refresh the existing curated `items_config` recipes against the latest menu
rather than generating every possible menu item.

The first implementation should:

- preserve configured categories, quantities, and chosen modifiers;
- update current item/modifier paths, titles, and prices;
- resolve modifier paths only inside their configured parent item;
- support explicit old-path-to-new-item overrides;
- produce a separate ambiguity/replacement report;
- validate every enabled simulator context; and
- back up and atomically install only a fully validated file.

Generating from scratch is unsafe until the parser retains prices, selection
rules, defaults, and required modifier groups.

## Direct EI validation

Add an approved EI endpoint or export if the business needs to distinguish:

- absent from EI;
- present in EI but inactive;
- present but not assigned to this menu; and
- present only in another context.

Keep this evidence separate from effective-menu validation.

## Multi-context availability matrix

Run a location across all supported channels and order types and produce a
matrix showing whether each PLU appears in every required context. Do not assume
one path is valid across contexts.

## Operator interface

After the CLI workflow is stable, a small internal UI could:

- select profiles;
- start a run;
- display safe and review counts;
- filter ambiguous/missing rows; and
- download a complete run bundle.

A UI would call the same service functions; it should not duplicate matching
logic.

## Scheduled monitoring

Potential later work:

- scheduled refresh and audit;
- retention policy for caches and run bundles;
- notification only when generation or review status changes;
- centrally managed secrets; and
- health/last-success dashboards.

Scheduling must preserve the same provenance and exit-code behavior as an
interactive run.

## Release engineering

Before distributing beyond the initial team:

- publish versioned internal releases;
- add a changelog and upgrade notes;
- test supported Python versions in CI;
- sign or checksum packaged releases;
- define ownership, escalation, and credential rotation procedures.
