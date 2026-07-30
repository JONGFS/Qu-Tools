from collections import Counter
import json

import pytest

from src.cache_manager import CacheManager
from src import cli


def make_profile_config(tmp_path):
    source = tmp_path / "inputs" / "Aloha.xlsx"
    source.parent.mkdir()
    source.write_bytes(b"workbook")
    config = tmp_path / "config" / "locations.json"
    config.parent.mkdir()
    config.write_text(
        json.dumps(
            {
                "profiles": {
                    "atlanta": {
                        "locationId": 11934,
                        "orderChannelId": 4685,
                        "orderTypeId": 4723,
                        "sourceWorkbook": "inputs/Aloha.xlsx",
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return config, source


def cache_menu(tmp_path):
    cache_directory = tmp_path / "cache"
    cache = CacheManager(cache_directory)
    menu = {
        "menuSnapshotId": "snapshot-1",
        "context": {
            "locationId": 11934,
            "orderChannelId": 4685,
            "orderTypeId": 4723,
        },
        "children": [],
    }
    cache.save_menu(
        "11934-4685-4723",
        menu,
        "generation-1",
    )
    return cache_directory, menu


def patch_offline_settings(monkeypatch):
    monkeypatch.setattr(
        cli,
        "_load_settings",
        lambda profile, env_file: pytest.fail(
            "offline command loaded credentials"
        ),
    )


def test_root_help_does_not_load_settings_or_call_network(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        cli,
        "_load_settings",
        lambda *args, **kwargs: pytest.fail(
            "--help loaded credentials"
        ),
    )
    monkeypatch.setattr(
        cli,
        "_refresh_menu",
        lambda *args, **kwargs: pytest.fail(
            "--help called the network"
        ),
    )

    with pytest.raises(SystemExit) as caught:
        cli.main(["--help"])

    assert caught.value.code == 0
    output = capsys.readouterr().out
    assert "refresh-menu" in output
    assert "check-plu" in output
    assert "parse-menu" in output
    assert "run" in output
    assert "status" in output


def test_subcommand_help_does_not_require_profile_file(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        cli,
        "_refresh_menu",
        lambda *args, **kwargs: pytest.fail(
            "--help called the network"
        ),
    )

    with pytest.raises(SystemExit) as caught:
        cli.main(["run", "--help"])

    assert caught.value.code == 0
    assert "--offline" in capsys.readouterr().out


def test_refresh_menu_loads_credentials_for_selected_profile(
    tmp_path,
    monkeypatch,
):
    config, _source = make_profile_config(tmp_path)
    cache_directory = tmp_path / "cache"
    selected = {}

    def fake_settings(profile, env_file):
        selected["profile"] = profile
        selected["env_file"] = env_file
        return object()

    def fake_refresh(settings, cache):
        menu = {
            "menuSnapshotId": "snapshot-2",
            "context": {
                "locationId": 11934,
                "orderChannelId": 4685,
                "orderTypeId": 4723,
            },
            "children": [],
        }
        cache.save_menu(
            "11934-4685-4723",
            menu,
            "generation-2",
        )
        return menu

    monkeypatch.setattr(cli, "_load_settings", fake_settings)
    monkeypatch.setattr(cli, "_refresh_menu", fake_refresh)

    result = cli.main(
        [
            "refresh-menu",
            "--location",
            "atlanta",
            "--config",
            str(config),
            "--cache-dir",
            str(cache_directory),
            "--env-file",
            str(tmp_path / ".env"),
        ]
    )

    assert result == 0
    assert selected["profile"].location_id == 11934
    assert selected["env_file"] == tmp_path / ".env"
    assert (
        cache_directory / "11934-4685-4723" / "menu.json"
    ).exists()


def test_parse_menu_uses_selected_cached_context(
    tmp_path,
    monkeypatch,
):
    config, _source = make_profile_config(tmp_path)
    cache_directory, _menu = cache_menu(tmp_path)
    runs_directory = tmp_path / "runs"
    patch_offline_settings(monkeypatch)

    def fake_export(menu_path, csv_path, json_path, metadata=None):
        assert menu_path.name == "menu.json"
        assert metadata["location"] == "atlanta"
        csv_path.write_text("itemMasterId\n100\n", encoding="utf-8")
        json_path.write_text("[]\n", encoding="utf-8")
        return 1

    monkeypatch.setattr(cli, "_export_menu", fake_export)

    result = cli.main(
        [
            "parse-menu",
            "--location",
            "atlanta",
            "--config",
            str(config),
            "--cache-dir",
            str(cache_directory),
            "--runs-dir",
            str(runs_directory),
        ]
    )

    assert result == 0
    run_directory = next((runs_directory / "atlanta").iterdir())
    manifest = json.loads(
        (run_directory / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["profile"]["contextKey"] == "11934-4685-4723"
    assert manifest["flattenedMenuRows"] == 1
    assert (run_directory / "flattened_menu.csv").exists()
    assert (run_directory / "flattened_menu.json").exists()


def test_offline_run_creates_complete_bundle_and_returns_review_code(
    tmp_path,
    monkeypatch,
):
    config, source = make_profile_config(tmp_path)
    cache_directory, _menu = cache_menu(tmp_path)
    runs_directory = tmp_path / "runs"
    patch_offline_settings(monkeypatch)
    monkeypatch.setattr(
        cli,
        "_refresh_menu",
        lambda *args, **kwargs: pytest.fail(
            "--offline called the network"
        ),
    )

    def fake_export_menu(menu_path, csv_path, json_path, metadata=None):
        assert menu_path.name == "menu.json"
        csv_path.write_text("title\nMilk\n", encoding="utf-8")
        json_path.write_text("[]\n", encoding="utf-8")
        return 1

    def fake_reconcile(
        source_workbook,
        menu_path,
        output_workbook,
        *,
        include_unmigrated,
        provenance,
    ):
        assert source_workbook == source.resolve()
        assert include_unmigrated is False
        assert provenance["profile"] == "atlanta"
        output_workbook.write_bytes(b"reconciled")
        return Counter({"MATCH": 3, "NOT_FOUND_IN_QU": 1})

    def fake_reports(workbook, all_csv, review_csv):
        all_csv.write_text("status\nMATCH\n", encoding="utf-8")
        review_csv.write_text(
            "status\nNOT_FOUND_IN_QU\n",
            encoding="utf-8",
        )
        return Counter({"MATCH": 3, "NOT_FOUND_IN_QU": 1}), 1

    monkeypatch.setattr(cli, "_export_menu", fake_export_menu)
    monkeypatch.setattr(cli, "_reconcile_workbook", fake_reconcile)
    monkeypatch.setattr(
        cli,
        "_export_reconciliation_reports",
        fake_reports,
    )

    result = cli.main(
        [
            "run",
            "--location",
            "atlanta",
            "--config",
            str(config),
            "--cache-dir",
            str(cache_directory),
            "--runs-dir",
            str(runs_directory),
            "--offline",
        ]
    )

    assert result == 2
    run_directory = next((runs_directory / "atlanta").iterdir())
    expected_files = {
        "flattened_menu.csv",
        "flattened_menu.json",
        "reconciled_mapping.xlsx",
        "plu_results.csv",
        "plu_review.csv",
        "summary.txt",
        "manifest.json",
    }
    assert expected_files <= {
        path.name for path in run_directory.iterdir()
    }
    manifest = json.loads(
        (run_directory / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["result"] == "review_required"
    assert manifest["reviewCount"] == 1
    assert manifest["inputs"]["menu"]["sha256"]
    assert manifest["inputs"]["sourceWorkbook"]["sha256"]


def test_status_is_offline_and_reports_missing_cache(
    tmp_path,
    monkeypatch,
    capsys,
):
    config, _source = make_profile_config(tmp_path)
    patch_offline_settings(monkeypatch)
    monkeypatch.setattr(
        cli,
        "_refresh_menu",
        lambda *args, **kwargs: pytest.fail(
            "status called the network"
        ),
    )

    result = cli.main(
        [
            "status",
            "--location",
            "atlanta",
            "--config",
            str(config),
            "--cache-dir",
            str(tmp_path / "cache"),
            "--runs-dir",
            str(tmp_path / "runs"),
        ]
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "Menu cache state: missing" in output
    assert "Latest run: (none)" in output
