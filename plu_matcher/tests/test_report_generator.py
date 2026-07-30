from collections import Counter
import csv

from openpyxl import Workbook
import pytest

from src.models import SAFE_RECONCILIATION_STATUSES
from src.reconciliation import AUDIT_HEADERS
from src.report_generator import export_reconciliation_reports


BASE_HEADERS = (
    "Number",
    "Long name",
    "Migrated to Qu?",
    "Qu Item ID",
    "Qu Item Name",
)
REPORT_HEADERS = (*BASE_HEADERS, *AUDIT_HEADERS)


def _make_workbook(path, rows, *, headers=REPORT_HEADERS):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Aloha > Qu Item Migration"
    for _ in range(7):
        sheet.append([])
    sheet.append(list(headers))
    for row in rows:
        sheet.append(
            [row.get(header) for header in headers]
        )
    workbook.save(path)
    workbook.close()


def _result_row(number, status):
    return {
        "Number": number,
        "Long name": f"Item {number}",
        "Migrated to Qu?": "Yes",
        "Qu Item ID": int(number) + 100,
        "Qu Item Name": f"QU Item {number}",
        "Reconciliation Status": status,
        "Previous Qu Item ID": None,
        "Previous Qu Item Name": None,
        "Proposed Qu Item ID": int(number) + 100,
        "Proposed Qu Item Name": f"QU Item {number}",
        "QU Path Count": 1,
        "Candidate QU Items": f"{int(number) + 100}: candidate",
        "Reconciliation Notes": "test",
    }


def _read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def test_reconciliation_export_writes_all_and_only_unsafe_review(
    tmp_path,
):
    workbook_path = tmp_path / "reconciled.xlsx"
    safe_statuses = sorted(
        status.value for status in SAFE_RECONCILIATION_STATUSES
    )
    rows = [
        _result_row(str(900001 + index), status)
        for index, status in enumerate(safe_statuses)
    ]
    rows.extend(
        [
            _result_row("900010", "AMBIGUOUS_QU_ITEM"),
            _result_row("900011", "FUTURE_UNSAFE_STATUS"),
            _result_row("900012", ""),
        ]
    )
    _make_workbook(workbook_path, rows)

    all_path = tmp_path / "reports" / "plu_results.csv"
    review_path = tmp_path / "reports" / "plu_review.csv"
    counts, review_count = export_reconciliation_reports(
        workbook_path,
        all_path,
        review_path,
    )

    expected_counts = Counter(safe_statuses)
    expected_counts.update(
        ["AMBIGUOUS_QU_ITEM", "FUTURE_UNSAFE_STATUS"]
    )
    assert counts == expected_counts
    assert review_count == 2

    all_rows = _read_csv(all_path)
    review_rows = _read_csv(review_path)
    assert len(all_rows) == len(safe_statuses) + 2
    assert {
        row["Reconciliation Status"] for row in review_rows
    } == {"AMBIGUOUS_QU_ITEM", "FUTURE_UNSAFE_STATUS"}
    assert all(
        row["Reconciliation Status"] not in safe_statuses
        for row in review_rows
    )
    assert all_rows[0]["Number"].isdigit()
    assert tuple(all_rows[0]) == REPORT_HEADERS


def test_reconciliation_export_normalizes_numeric_plu(tmp_path):
    workbook_path = tmp_path / "reconciled.xlsx"
    _make_workbook(
        workbook_path,
        [_result_row(916226.0, "MATCH")],
    )

    all_path = tmp_path / "all.csv"
    review_path = tmp_path / "review.csv"
    counts, review_count = export_reconciliation_reports(
        workbook_path,
        all_path,
        review_path,
    )

    assert counts == Counter({"MATCH": 1})
    assert review_count == 0
    assert _read_csv(all_path)[0]["Number"] == "916226"
    assert _read_csv(review_path) == []


def test_reconciliation_export_preserves_zero_identifier(tmp_path):
    workbook_path = tmp_path / "reconciled.xlsx"
    _make_workbook(
        workbook_path,
        [_result_row(0, "MATCH")],
    )

    all_path = tmp_path / "all.csv"
    export_reconciliation_reports(
        workbook_path,
        all_path,
        tmp_path / "review.csv",
    )

    assert _read_csv(all_path)[0]["Number"] == "0"


def test_reconciliation_export_rejects_missing_audit_column(tmp_path):
    workbook_path = tmp_path / "incomplete.xlsx"
    incomplete_headers = tuple(
        header
        for header in REPORT_HEADERS
        if header != "Reconciliation Notes"
    )
    _make_workbook(
        workbook_path,
        [],
        headers=incomplete_headers,
    )

    with pytest.raises(
        ValueError,
        match="Reconciliation Notes",
    ):
        export_reconciliation_reports(
            workbook_path,
            tmp_path / "all.csv",
            tmp_path / "review.csv",
        )

    assert not (tmp_path / "all.csv").exists()
    assert not (tmp_path / "review.csv").exists()
