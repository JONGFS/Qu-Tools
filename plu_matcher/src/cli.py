"""Unified command-line interface for the Aloha-to-QU handoff tool."""

from __future__ import annotations

import argparse
from collections import Counter
from importlib.metadata import PackageNotFoundError, version
import json
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any, Mapping, Sequence

from .cache_manager import CacheManager
from .models import SAFE_RECONCILIATION_STATUSES
from .profiles import (
    DEFAULT_PROFILES_PATH,
    LocationProfile,
    get_profile,
)
from .run_manager import (
    create_run_directory,
    file_record,
    write_json,
    write_text,
)

if TYPE_CHECKING:
    from .settings import Settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CACHE_DIRECTORY = PROJECT_ROOT / "cache"
DEFAULT_RUNS_DIRECTORY = PROJECT_ROOT / "runs"
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


def _tool_version() -> str:
    try:
        return version("qu-tools")
    except PackageNotFoundError:
        return "development"


def _load_settings(
    profile: LocationProfile,
    env_file: Path,
) -> Settings:
    from .settings import load_settings

    return load_settings(
        location_id=profile.location_id,
        order_channel_id=profile.order_channel_id,
        order_type_id=profile.order_type_id,
        env_file=env_file,
    )


def _refresh_menu(settings: Settings, cache: CacheManager) -> dict:
    from .main import refresh_menu

    return refresh_menu(settings=settings, cache=cache)


def _reconcile_workbook(
    source_workbook: Path,
    menu_path: Path,
    output_workbook: Path,
    *,
    include_unmigrated: bool,
    provenance: dict[str, Any],
) -> Counter:
    from .reconciliation import reconcile_workbook

    return reconcile_workbook(
        source_workbook=source_workbook,
        menu_path=menu_path,
        output_workbook=output_workbook,
        include_unmigrated=include_unmigrated,
        provenance=provenance,
    )


def _export_menu(
    menu_path: Path,
    csv_path: Path,
    json_path: Path,
    metadata: Mapping[str, Any] | None = None,
) -> int:
    from .menu_export import export_cached_menu

    return export_cached_menu(
        menu_path,
        csv_path,
        json_path,
        metadata=metadata,
    )


def _export_reconciliation_reports(
    workbook_path: Path,
    all_csv_path: Path,
    review_csv_path: Path,
) -> tuple[Counter, int]:
    from .report_generator import export_reconciliation_reports

    return export_reconciliation_reports(
        workbook_path,
        all_csv_path,
        review_csv_path,
    )


def _add_profile_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--location",
        required=True,
        metavar="PROFILE",
        help="Location profile name from config/locations.json.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_PROFILES_PATH,
        help=f"Location profile JSON (default: {DEFAULT_PROFILES_PATH}).",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=DEFAULT_CACHE_DIRECTORY,
        help=f"Menu cache root (default: {DEFAULT_CACHE_DIRECTORY}).",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=DEFAULT_ENV_FILE,
        help=f"Credential .env file (default: {DEFAULT_ENV_FILE}).",
    )


def _add_artifact_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=DEFAULT_RUNS_DIRECTORY,
        help=f"Run artifact root (default: {DEFAULT_RUNS_DIRECTORY}).",
    )


def _add_reconciliation_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--source",
        type=Path,
        help="Override the source workbook configured for the profile.",
    )
    parser.add_argument(
        "--include-unmigrated",
        action="store_true",
        help=(
            "Also reconcile rows not currently marked 'Migrated to Qu? = "
            "Yes'. The default audits migrated rows only."
        ),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qu-tools",
        description=(
            "Refresh QU menus, validate Aloha PLUs, and export a "
            "flattened cached menu."
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    refresh_parser = subparsers.add_parser(
        "refresh-menu",
        help="Request the latest menu for a location profile.",
    )
    _add_profile_arguments(refresh_parser)
    refresh_parser.set_defaults(handler=_handle_refresh_menu)

    check_parser = subparsers.add_parser(
        "check-plu",
        help="Reconcile the profile workbook against its cached menu.",
    )
    _add_profile_arguments(check_parser)
    _add_artifact_arguments(check_parser)
    _add_reconciliation_arguments(check_parser)
    check_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Request the latest menu before checking PLUs.",
    )
    check_parser.set_defaults(handler=_handle_check_plu)

    parse_parser = subparsers.add_parser(
        "parse-menu",
        help="Export the profile's cached nested menu as CSV and JSON.",
    )
    _add_profile_arguments(parse_parser)
    _add_artifact_arguments(parse_parser)
    parse_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Request the latest menu before exporting it.",
    )
    parse_parser.set_defaults(handler=_handle_parse_menu)

    run_parser = subparsers.add_parser(
        "run",
        help="Refresh, reconcile, parse, and create one audit bundle.",
    )
    _add_profile_arguments(run_parser)
    _add_artifact_arguments(run_parser)
    _add_reconciliation_arguments(run_parser)
    run_parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the existing cache without contacting QU.",
    )
    run_parser.set_defaults(handler=_handle_run)

    status_parser = subparsers.add_parser(
        "status",
        help="Show configured inputs, cache state, and the latest run.",
    )
    _add_profile_arguments(status_parser)
    _add_artifact_arguments(status_parser)
    status_parser.set_defaults(handler=_handle_status)
    return parser


def _context(
    args: argparse.Namespace,
) -> tuple[LocationProfile, CacheManager]:
    profile = get_profile(args.location, args.config)
    return profile, CacheManager(args.cache_dir)


def _validate_menu_context(
    menu: dict,
    profile: LocationProfile,
) -> None:
    """Reject a cache that declares a different location/context."""
    context = menu.get("context")
    if not isinstance(context, dict):
        return

    expected = {
        "locationId": profile.location_id,
        "orderChannelId": profile.order_channel_id,
        "orderTypeId": profile.order_type_id,
    }
    mismatches = []
    for field, expected_value in expected.items():
        actual_value = context.get(field)
        if actual_value in (None, ""):
            continue
        try:
            matches = int(actual_value) == expected_value
        except (TypeError, ValueError):
            matches = False
        if not matches:
            mismatches.append(
                f"{field}={actual_value!r} (expected {expected_value})"
            )
    if mismatches:
        raise RuntimeError(
            "Cached menu context does not match the selected profile: "
            + ", ".join(mismatches)
        )


def _load_menu(
    *,
    profile: LocationProfile,
    settings: Settings | None,
    cache: CacheManager,
    refresh: bool,
) -> tuple[dict, Path, dict]:
    if refresh:
        if settings is None:
            raise RuntimeError(
                "Internal error: network refresh requires QU settings."
            )
        menu = _refresh_menu(settings, cache)
    else:
        menu = cache.load_menu(profile.context_key)
    _validate_menu_context(menu, profile)
    return (
        menu,
        cache.menu_path(profile.context_key),
        cache.load_metadata(profile.context_key),
    )


def _source_workbook(
    args: argparse.Namespace,
    profile: LocationProfile,
) -> Path:
    source = args.source if args.source is not None else profile.source_workbook
    source = Path(source).resolve()
    if not source.exists():
        raise FileNotFoundError(
            f"Source workbook was not found for profile "
            f"{profile.name!r}: {source}"
        )
    if not source.is_file():
        raise ValueError(f"Source workbook is not a file: {source}")
    return source


def _status_text(status: Any) -> str:
    return str(getattr(status, "value", status))


def _serializable_counts(counts: Mapping[Any, int]) -> dict[str, int]:
    return {
        _status_text(status): int(count)
        for status, count in sorted(
            counts.items(),
            key=lambda item: _status_text(item[0]),
        )
    }


def _review_count_from_counts(counts: Mapping[Any, int]) -> int:
    safe_values = {
        _status_text(status)
        for status in SAFE_RECONCILIATION_STATUSES
    }
    return sum(
        int(count)
        for status, count in counts.items()
        if _status_text(status) not in safe_values
    )


def _provenance(
    *,
    profile: LocationProfile,
    metadata: Mapping[str, Any],
    menu: Mapping[str, Any],
    source_workbook: Path,
    created_at_iso: str,
) -> dict[str, Any]:
    return {
        "profile": profile.name,
        "location_id": profile.location_id,
        "order_channel_id": profile.order_channel_id,
        "order_type_id": profile.order_type_id,
        "menu_snapshot_id": menu.get("menuSnapshotId"),
        "generation_time": metadata.get("generation_time"),
        "last_checked_at": metadata.get("last_checked_at"),
        "source_workbook": str(source_workbook),
        "source_workbook_sha256": file_record(source_workbook)["sha256"],
        "run_timestamp": created_at_iso,
        "tool_version": _tool_version(),
    }


def _menu_export_metadata(
    profile: LocationProfile,
    metadata: Mapping[str, Any],
    menu: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "location": profile.name,
        "location_id": profile.location_id,
        "order_channel_id": profile.order_channel_id,
        "order_type_id": profile.order_type_id,
        "menu_snapshot_id": menu.get("menuSnapshotId"),
        "generation_time": metadata.get("generation_time"),
        "last_checked_at": metadata.get("last_checked_at"),
    }


def _artifact_records(paths: Mapping[str, Path]) -> dict[str, Any]:
    return {
        name: file_record(path)
        for name, path in paths.items()
        if path.exists()
    }


def _base_manifest(
    *,
    command: str,
    profile: LocationProfile,
    created_at_iso: str,
    menu: Mapping[str, Any],
    metadata: Mapping[str, Any],
    menu_path: Path,
    config_path: Path,
) -> dict[str, Any]:
    inputs: dict[str, Any] = {
        "menu": file_record(menu_path),
    }
    if config_path.exists():
        inputs["locationProfiles"] = file_record(config_path)
    metadata_path = menu_path.with_name("metadata.json")
    if metadata_path.exists():
        inputs["menuMetadata"] = file_record(metadata_path)

    return {
        "schemaVersion": 1,
        "tool": "qu-tools",
        "toolVersion": _tool_version(),
        "command": command,
        "createdAt": created_at_iso,
        "profile": profile.as_dict(),
        "menu": {
            "snapshotId": menu.get("menuSnapshotId"),
            "generationTime": metadata.get("generation_time"),
            "lastCheckedAt": metadata.get("last_checked_at"),
            "lastCheckResult": metadata.get("last_check_result"),
        },
        "inputs": inputs,
    }


def _run_reconciliation(
    *,
    args: argparse.Namespace,
    profile: LocationProfile,
    menu: dict,
    menu_path: Path,
    metadata: Mapping[str, Any],
    run_directory: Path,
    created_at_iso: str,
) -> tuple[dict[str, Path], dict[str, int], int]:
    source = _source_workbook(args, profile)
    output_workbook = run_directory / "reconciled_mapping.xlsx"
    all_csv = run_directory / "plu_results.csv"
    review_csv = run_directory / "plu_review.csv"
    provenance = _provenance(
        profile=profile,
        metadata=metadata,
        menu=menu,
        source_workbook=source,
        created_at_iso=created_at_iso,
    )
    reconciliation_counts = _reconcile_workbook(
        source,
        menu_path,
        output_workbook,
        include_unmigrated=args.include_unmigrated,
        provenance=provenance,
    )
    report_counts, report_review_count = (
        _export_reconciliation_reports(
            output_workbook,
            all_csv,
            review_csv,
        )
    )
    counts = (
        report_counts
        if report_counts is not None
        else reconciliation_counts
    )
    review_count = (
        int(report_review_count)
        if report_review_count is not None
        else _review_count_from_counts(counts)
    )
    return (
        {
            "sourceWorkbook": source,
            "reconciledWorkbook": output_workbook,
            "pluResultsCsv": all_csv,
            "pluReviewCsv": review_csv,
        },
        _serializable_counts(counts),
        review_count,
    )


def _write_run_bundle(
    *,
    command: str,
    args: argparse.Namespace,
    profile: LocationProfile,
    menu: dict,
    menu_path: Path,
    metadata: Mapping[str, Any],
    run_directory: Path,
    created_at_iso: str,
    output_paths: dict[str, Path],
    counts: Mapping[str, int] | None = None,
    review_count: int = 0,
    menu_node_count: int | None = None,
) -> None:
    result = "review_required" if review_count else "passed"
    summary_lines = [
        "QU Tools run summary",
        f"Command: {command}",
        f"Profile: {profile.name}",
        f"Context: {profile.context_key}",
        f"Menu snapshot: {menu.get('menuSnapshotId') or '(unknown)'}",
        (
            "Menu generation: "
            f"{metadata.get('generation_time') or '(unknown)'}"
        ),
    ]
    if menu_node_count is not None:
        summary_lines.append(f"Flattened menu rows: {menu_node_count}")
    if counts is not None:
        summary_lines.append("Reconciliation:")
        summary_lines.extend(
            f"  {status}: {count}"
            for status, count in sorted(counts.items())
        )
        summary_lines.append(f"Manual review rows: {review_count}")
    summary_lines.extend(
        [
            f"Result: {result.upper()}",
            f"Artifacts: {run_directory.resolve()}",
        ]
    )
    summary_path = run_directory / "summary.txt"
    write_text(summary_path, "\n".join(summary_lines))
    output_paths["summary"] = summary_path

    manifest = _base_manifest(
        command=command,
        profile=profile,
        created_at_iso=created_at_iso,
        menu=menu,
        metadata=metadata,
        menu_path=menu_path,
        config_path=args.config,
    )
    manifest["result"] = result
    manifest["reviewCount"] = review_count
    if counts is not None:
        manifest["reconciliationCounts"] = dict(counts)
    if menu_node_count is not None:
        manifest["flattenedMenuRows"] = menu_node_count
    source_workbook = output_paths.get("sourceWorkbook")
    if source_workbook is not None:
        manifest["inputs"]["sourceWorkbook"] = file_record(
            source_workbook
        )
    manifest["outputs"] = _artifact_records(
        {
            name: path
            for name, path in output_paths.items()
            if name != "sourceWorkbook"
        }
    )
    write_json(run_directory / "manifest.json", manifest)


def _handle_refresh_menu(args: argparse.Namespace) -> int:
    profile, cache = _context(args)
    settings = _load_settings(profile, args.env_file)
    menu, menu_path, metadata = _load_menu(
        profile=profile,
        settings=settings,
        cache=cache,
        refresh=True,
    )
    print(f"Profile: {profile.name}")
    print(f"Context: {profile.context_key}")
    print(f"Snapshot ID: {menu.get('menuSnapshotId')}")
    print(f"Generation time: {metadata.get('generation_time')}")
    print(f"Cache: {menu_path.resolve()}")
    return 0


def _handle_check_plu(args: argparse.Namespace) -> int:
    profile, cache = _context(args)
    settings = (
        _load_settings(profile, args.env_file)
        if args.refresh
        else None
    )
    menu, menu_path, metadata = _load_menu(
        profile=profile,
        settings=settings,
        cache=cache,
        refresh=args.refresh,
    )
    run_directory, created_at = create_run_directory(
        args.runs_dir,
        profile.name,
    )
    created_at_iso = created_at.isoformat()
    output_paths, counts, review_count = _run_reconciliation(
        args=args,
        profile=profile,
        menu=menu,
        menu_path=menu_path,
        metadata=metadata,
        run_directory=run_directory,
        created_at_iso=created_at_iso,
    )
    _write_run_bundle(
        command="check-plu",
        args=args,
        profile=profile,
        menu=menu,
        menu_path=menu_path,
        metadata=metadata,
        run_directory=run_directory,
        created_at_iso=created_at_iso,
        output_paths=output_paths,
        counts=counts,
        review_count=review_count,
    )
    print(f"PLU check complete: {run_directory.resolve()}")
    print(f"Manual review rows: {review_count}")
    return 2 if review_count else 0


def _handle_parse_menu(args: argparse.Namespace) -> int:
    profile, cache = _context(args)
    settings = (
        _load_settings(profile, args.env_file)
        if args.refresh
        else None
    )
    menu, menu_path, metadata = _load_menu(
        profile=profile,
        settings=settings,
        cache=cache,
        refresh=args.refresh,
    )
    run_directory, created_at = create_run_directory(
        args.runs_dir,
        profile.name,
    )
    csv_path = run_directory / "flattened_menu.csv"
    json_path = run_directory / "flattened_menu.json"
    menu_node_count = _export_menu(
        menu_path,
        csv_path,
        json_path,
        metadata=_menu_export_metadata(profile, metadata, menu),
    )
    output_paths = {
        "flattenedMenuCsv": csv_path,
        "flattenedMenuJson": json_path,
    }
    _write_run_bundle(
        command="parse-menu",
        args=args,
        profile=profile,
        menu=menu,
        menu_path=menu_path,
        metadata=metadata,
        run_directory=run_directory,
        created_at_iso=created_at.isoformat(),
        output_paths=output_paths,
        menu_node_count=menu_node_count,
    )
    print(f"Menu export complete: {run_directory.resolve()}")
    print(f"Flattened menu rows: {menu_node_count}")
    return 0


def _handle_run(args: argparse.Namespace) -> int:
    profile, cache = _context(args)
    settings = (
        None
        if args.offline
        else _load_settings(profile, args.env_file)
    )
    menu, menu_path, metadata = _load_menu(
        profile=profile,
        settings=settings,
        cache=cache,
        refresh=not args.offline,
    )
    run_directory, created_at = create_run_directory(
        args.runs_dir,
        profile.name,
    )
    created_at_iso = created_at.isoformat()

    csv_path = run_directory / "flattened_menu.csv"
    json_path = run_directory / "flattened_menu.json"
    menu_node_count = _export_menu(
        menu_path,
        csv_path,
        json_path,
        metadata=_menu_export_metadata(profile, metadata, menu),
    )
    output_paths, counts, review_count = _run_reconciliation(
        args=args,
        profile=profile,
        menu=menu,
        menu_path=menu_path,
        metadata=metadata,
        run_directory=run_directory,
        created_at_iso=created_at_iso,
    )
    output_paths.update(
        {
            "flattenedMenuCsv": csv_path,
            "flattenedMenuJson": json_path,
        }
    )
    _write_run_bundle(
        command="run",
        args=args,
        profile=profile,
        menu=menu,
        menu_path=menu_path,
        metadata=metadata,
        run_directory=run_directory,
        created_at_iso=created_at_iso,
        output_paths=output_paths,
        counts=counts,
        review_count=review_count,
        menu_node_count=menu_node_count,
    )
    print(f"Run complete: {run_directory.resolve()}")
    print(f"Manual review rows: {review_count}")
    return 2 if review_count else 0


def _handle_status(args: argparse.Namespace) -> int:
    profile, cache = _context(args)
    menu_path = cache.menu_path(profile.context_key)
    metadata = cache.load_metadata(profile.context_key)
    print(f"Profile: {profile.name}")
    print(f"Context: {profile.context_key}")
    print(f"Source workbook: {profile.source_workbook}")
    print(
        "Source workbook state: "
        f"{'ready' if profile.source_workbook.is_file() else 'missing'}"
    )
    print(f"Menu cache: {menu_path.resolve()}")
    print(f"Menu cache state: {'ready' if metadata else 'missing'}")
    if metadata:
        print(f"Snapshot ID: {metadata.get('menu_snapshot_id')}")
        print(f"Generation time: {metadata.get('generation_time')}")
        print(f"Last checked: {metadata.get('last_checked_at')}")

    profile_runs = Path(args.runs_dir) / profile.name
    run_directories = (
        sorted(
            (
                path
                for path in profile_runs.iterdir()
                if path.is_dir()
            ),
            key=lambda path: path.name,
        )
        if profile_runs.is_dir()
        else []
    )
    latest_run = run_directories[-1] if run_directories else None
    print(
        "Latest run: "
        f"{latest_run.resolve() if latest_run else '(none)'}"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Parse CLI arguments and return a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (
        FileNotFoundError,
        json.JSONDecodeError,
        PermissionError,
        RuntimeError,
        ValueError,
    ) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
