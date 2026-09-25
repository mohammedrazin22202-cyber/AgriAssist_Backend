"""Tests for Contingency Protocol (Code Name: Plastic Man)
Verifies owner authentication, author credentials, and all 21 secret author codes.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app, PLASTIC_MAN_SECRET_CODES
from cli import check_cli_contingency

client = TestClient(app)

EXPECTED_CODES = [
    "29082003", "05051970", "22102022", "05082023", "05042025",
    "12112021", "20012026", "13092026", "7200170345", "9962830634",
    "9840503469", "8939887236", "9840019278", "7695966500", "6380376354",
    "9791060348", "9176101274", "9884602849", "9840714441", "8072761448",
    "9884783437"
]


def test_21_secret_codes_registry():
    """Verify all 21 secret author codes are correctly registered in the system."""
    assert len(PLASTIC_MAN_SECRET_CODES) == 21
    assert PLASTIC_MAN_SECRET_CODES == EXPECTED_CODES


def test_contingency_endpoint_all_21_codes():
    """Verify that every single one of the 21 codes successfully verifies against the API."""
    for idx, code in enumerate(EXPECTED_CODES, 1):
        res = client.get(f"/api/contingency-protocol?code={code}")
        assert res.status_code == 200
        data = res.json()
        assert data["contingency_activated"] is True
        assert data["is_valid_author_key"] is True
        assert data["key_index"] == idx
        assert data["real_owner_name"] == "MegaTron alias Mohammed Razin H"
        assert data["real_project_name"] == "AgriAssist"
        assert data["author_credentials"]["author"] == "Mohammed Razin H"
        assert data["author_credentials"]["contact"] == "mohammedrazin22202@gmail.com"
        assert data["author_credentials"]["linkedin"] == "https://www.linkedin.com/in/razin88307"
        assert data["author_credentials"]["github"] == "https://github.com/mohammedrazin22202-cyber"


def test_contingency_endpoint_alias():
    """Verify code name 'plastic man' and 'plasticman' activate the protocol."""
    for alias in ["plastic man", "plasticman", "megatron"]:
        res = client.get(f"/api/plastic-man?code={alias}")
        assert res.status_code == 200
        data = res.json()
        assert data["contingency_activated"] is True
        assert data["is_valid_author_key"] is True
        assert data["real_owner_name"] == "MegaTron alias Mohammed Razin H"


def test_cli_contingency_checker():
    """Verify CLI contingency checker function catches all 21 codes."""
    for code in EXPECTED_CODES:
        assert check_cli_contingency(code) is True
    assert check_cli_contingency("plastic man") is True
    assert check_cli_contingency("random_input_123") is False
