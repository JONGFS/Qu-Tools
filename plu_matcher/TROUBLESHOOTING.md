# Troubleshooting

Start with:

```powershell
.\run.cmd status --location atlanta
```

Then run the failed command with `--help` to confirm its syntax. Help and status
must not make a live menu request.

## `run.cmd` says the environment is not installed

Run:

```powershell
.\setup.cmd
```

If Python cannot be found, install Python 3.11 or newer and ensure either `py`
or `python` is available on `PATH`.

The `.cmd` launchers do not invoke PowerShell scripts and work with an
`AllSigned` PowerShell policy. Use them instead of the optional `.ps1` files;
do not weaken a machine-wide policy for this tool.

## `qu-tools` is not recognized

Either use the wrapper:

```powershell
.\run.cmd run --location atlanta
```

or call the environment's Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m src.cli --help
```

## Dependency installation fails

The first `setup.cmd` run installs the packages declared in `pyproject.toml`.
Connect to the approved corporate network or Python package index, then retry.
The offline demo avoids QU API calls after setup; it is not an offline package
installer.

## Missing environment variables

Compare `.env` with `.env.example`. Required secret-bearing settings are:

```text
QU_CLIENT_ID
QU_CLIENT_SECRET
QU_X_INTEGRATION
```

`QU_BASE_URL` must point to the approved QU v4 gateway. Location, channel, and
order-type IDs belong in `config/locations.json`, not `.env`.

For production, use the host only:

```dotenv
QU_BASE_URL=https://gateway-api.qubeyond.com
```

The client adds `/api/v4` to endpoint paths. Including `/api/v4` in the setting
would create a duplicated path.

Do not paste credential values into logs, tickets, Git commits, or run bundles.

## `401 Unauthorized`

Check that:

- `grant_type` is `client_credentials`;
- `QU_CLIENT_ID` is the client ID, not a location ID;
- `QU_CLIENT_SECRET` contains the current Qu SID/client secret;
- there are no surrounding quotes or copied spaces; and
- the credential is valid for the selected QU environment.

Request a replacement through the approved internal credential process if the
secret is expired or revoked. Do not add access tokens to `.env`; the client
requests a token at runtime.

## `403 Forbidden`

Authentication succeeded, but the integration may not be authorized for the
selected location or endpoint. Verify `QU_X_INTEGRATION` and the profile's
location with the QU integration owner.

## No cached menu exists

Create it with:

```powershell
.\run.cmd refresh-menu --location atlanta
```

`check-plu` and `parse-menu` require a complete context cache. `run` refreshes
before using the cache.

## The API says the menu is unchanged

This is expected when QU returns no new generation for `PrevGenerationTime`.
Check `status`: `last_checked_at` should be recent while `generation_time` can
remain older. The existing complete menu remains authoritative for that check.

## Results look stale or two reports differ

The usual cause is comparing artifacts produced from different menu
generations or workbooks. Run:

```powershell
.\run.cmd run --location atlanta
```

Then use only files inside the new timestamped run directory. Confirm the
manifest's location, snapshot, generation time, and source workbook.

## Korean combo or another combo appears on many paths

One sellable QU item can occur beneath several combo containers. The PLU
reconciler groups those occurrences by item ID:

- one PLU and one item ID is an identity match;
- several paths can still require path-level review; and
- one PLU on several distinct IDs is ambiguous.

Do not count every path as a separate identity mismatch.

## An EI item is missing from the report

The tool checks the effective menu, not the complete EI database. Confirm:

- the location;
- order channel;
- order type;
- whether the item is active and assigned to that menu context; and
- whether a different profile returns it.

Direct EI verification requires an EI endpoint or approved export and is outside
the current tool.

## Workbook or worksheet not found

Check the location's `sourceWorkbook` in `config/locations.json`. Relative paths
are resolved from the project directory.

The workbook must include:

```text
Aloha > Qu Item Migration
```

The expected header row must contain at least:

```text
Number
Long name
Migrated to Qu?
Qu Item ID
Qu Item Name
```

Spelling, punctuation, and question marks matter.

## `PermissionError` when writing a workbook

Close the generated workbook in Excel, File Explorer preview, and any process
syncing or inspecting it, then retry. OneDrive can briefly lock newly written
files; wait for synchronization to finish if necessary.

The tool never needs permission to overwrite the source workbook.

## `KeyError: 'Migrated to Qu?'`

The configured sheet/header row does not contain the exact required header, or
the wrong workbook was selected. Correct the workbook or profile rather than
hard-coding a different column index.

## Test import errors or "file not found"

From `plu_matcher`:

```powershell
python -m pytest
```

From the repository root:

```powershell
python -m pytest .\plu_matcher\tests
```

Do not use `tests/test_...` from the repository root because the tests live
under `plu_matcher/tests`.

## Exit code `2`

The run completed and produced usable evidence, but at least one row needs
manual review. Open the summary/review artifacts in that same run directory.
Exit `2` is not an API or installation failure.
