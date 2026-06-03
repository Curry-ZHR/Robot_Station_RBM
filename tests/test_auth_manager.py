from modules.auth.session import RobotAuthManager


def _users_file(tmp_path):
    path = tmp_path / "users.txt"
    path.write_text("zhuzl:idata2026\ncaizj:idata2026\n", encoding="utf-8")
    return path


def test_login_conflict_and_force_revokes_previous_session(tmp_path):
    manager = RobotAuthManager(user_file=_users_file(tmp_path), timeout_sec=30)

    first, first_token = manager.login("zhuzl", "idata2026", client="desk-a")
    assert first["ok"]
    assert first["code"] == "AUTH-LOGIN"
    assert first_token

    conflict, conflict_token = manager.login("caizj", "idata2026", client="desk-b")
    assert not conflict["ok"]
    assert conflict["code"] == "AUTH-CONFLICT"
    assert conflict["active"]["user"] == "zhuzl"
    assert conflict_token is None

    forced, forced_token = manager.login("caizj", "idata2026", force=True, client="desk-b")
    assert forced["ok"]
    assert forced["code"] == "AUTH-FORCED"
    assert forced["revokedUser"] == "zhuzl"
    assert forced_token

    old_status = manager.status(first_token)
    assert old_status["code"] == "AUTH-REVOKED"
    assert old_status["revokedBy"] == "caizj"

    new_status = manager.status(forced_token)
    assert new_status["authenticated"]
    assert new_status["user"] == "caizj"


def test_invalid_password_is_rejected(tmp_path):
    manager = RobotAuthManager(user_file=_users_file(tmp_path), timeout_sec=30)

    result, token = manager.login("zhuzl", "wrong")

    assert not result["ok"]
    assert result["code"] == "AUTH-INVALID"
    assert token is None
