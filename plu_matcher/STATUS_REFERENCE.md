# Status Reference

QU Tools separates identity reconciliation from path resolution. A PLU can
identify the correct QU item while that item still appears on several menu
paths.

## Reconciliation statuses

### Safe

`MATCH`

The exact normalized Aloha PLU belongs to one active QU item ID on one current
menu path. The generated mapping can use that ID.

`MATCH_MULTIPLE_PATHS`

The exact PLU belongs to one QU item ID, but that item occurs on multiple menu
paths. The identity is safe. A downstream process that needs one specific
`itemPathKey` must still choose or review the path.

`PLU_MATCH_ID_UPDATED`

The exact PLU uniquely identifies one current QU item ID, but the source
workbook stored a different ID. Because reconciliation is PLU-first, the
generated workbook replaces the stale derived ID. This commonly corrects a
mapping that pointed to a combo container instead of its nested sellable item.

### Manual review

`AMBIGUOUS_QU_ITEM`

The exact PLU appears on more than one distinct QU item ID. The tool will not
guess which identity is correct.

`EXISTING_MAPPING_CONFLICT`

The stored mapping and proposed evidence conflict under a rule that is not safe
to apply automatically. This remains for compatibility with older or more
restrictive reconciliation results.

`PLU_MISMATCH_REVIEW`

The source has a QU item ID, but the current PLU on that item does not equal the
expected Aloha PLU. Review the Aloha record and all current regular/combo paths.

`NOT_FOUND_IN_QU`

The Aloha PLU has no exact match in the current effective menu, and the source
does not provide a usable current item ID.

`NOT_FOUND_IN_CURRENT_CONTEXT`

The workbook's QU item ID is absent from this location/channel/order-type menu.
It may exist elsewhere in EI or another context; this tool cannot prove that.

## Path-resolution statuses

`MATCHED`

The safe mapping resolved to one current menu node.

`UNCHANGED`

The approved stored path equals the selected current path.

`UPDATED`

The identity is safe and a current path differs from the stored path. Review the
generated path evidence before using it in an ordering configuration.

`MISSING`

No current menu path could be resolved for the safe identity.

`AMBIGUOUS`

More than one current path remains and the tool has insufficient evidence to
choose one.

`PLU_MISMATCH`

The path candidate's PLU does not equal the approved Aloha PLU.

`REVIEW`

A non-specific condition requires an operator decision.

## Safe does not mean globally configured

Safe statuses only describe evidence in the requested effective menu. They do
not certify:

- every EI record;
- another location;
- another channel or order type;
- a disabled item; or
- a future menu generation.

Run each required location/context profile independently.

## Exit-code relationship

- Exit `0`: the requested operation completed with no review result.
- Exit `1`: the operation could not complete.
- Exit `2`: artifacts were generated, but at least one result has a manual
  review status.
