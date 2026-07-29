# QU Item Path Refresher — Starter

## Goal
Build a Python tool that:
1. Authenticates with QU.
2. Downloads the context-specific menu.
3. Saves the menu and `X-Generation-Time`.
4. Uses `PrevGenerationTime` to avoid unnecessary downloads.
5. Flattens the menu hierarchy.
6. Loads approved mappings from Excel.
7. Matches by QU Item ID first and PLU second.
8. Compares stored and current `itemPathKey`.
9. Generates a report and refreshed simulator JSON.

## Build order
1. API + cache
2. Menu parser
3. Excel loader
4. Matching
5. Path comparison
6. Report
7. Simulator config

Start with five test items, expand to twenty, then run the full workbook.

## Current workflow

From the `plu_matcher` directory, run:

```powershell
python -m scripts.run_workflow
```

This command uses:

- `private_data/response+Alc.json` as the current QU menu.
- `private_data/Aloha_Qu_Menu_In_Progress.xlsx` as the Aloha source.
- `outputs/Aloha_Qu_Menu_Reconciled.xlsx` as the generated, auditable mapping workbook.

The path matcher loads only safe reconciliation results (`MATCH` and
`MATCH_MULTIPLE_PATHS`). Ambiguous identities, existing mapping conflicts,
PLU mismatches, and missing items stay out of automatic path matching.

Review identity problems with:

```powershell
python -m scripts.print_reconciliation_review
```

Review safe identities that have multiple current menu paths with:

```powershell
python -m scripts.print_path_review
```

Command to find PLU differences.
cd plu_matcher
python -m scripts.print_reconciliation_review --workbook outputs/Aloha_Qu_Menu_Reconciled_Harmonized.xlsx | Select-String "Status=PLU_MISMATCH_REVIEW"
