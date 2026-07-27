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
