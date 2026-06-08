from __future__ import annotations

import base64

import pytest

from dragkraft.dashboard.uploads import UploadError, save_uploaded_workbook


def test_save_uploaded_workbook_decodes_excel_content_to_stable_path(tmp_path) -> None:
    payload = b"excel-bytes"
    contents = "data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,"
    contents += base64.b64encode(payload).decode("ascii")

    path = save_uploaded_workbook(
        contents=contents,
        filename="New Profile.xlsx",
        upload_dir=tmp_path,
    )

    assert path.name.startswith("New_Profile-")
    assert path.suffix == ".xlsx"
    assert path.read_bytes() == payload


def test_save_uploaded_workbook_rejects_unsupported_file_type(tmp_path) -> None:
    contents = "data:text/plain;base64," + base64.b64encode(b"x").decode("ascii")

    with pytest.raises(UploadError, match="Excel workbook"):
        save_uploaded_workbook(
            contents=contents,
            filename="profile.csv",
            upload_dir=tmp_path,
        )


def test_save_uploaded_workbook_rejects_invalid_payload(tmp_path) -> None:
    with pytest.raises(UploadError, match="Invalid upload payload"):
        save_uploaded_workbook(
            contents="not-base64",
            filename="profile.xlsx",
            upload_dir=tmp_path,
        )
