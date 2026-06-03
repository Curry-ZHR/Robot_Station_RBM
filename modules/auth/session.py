"""Lightweight single-operator auth for the local Robot Station console."""

import os
import secrets
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_USER_FILE = ROOT_DIR / "config" / "users.txt"
DEFAULT_TIMEOUT_SEC = float(os.environ.get("ROBOT_STATION_AUTH_TIMEOUT_SEC", "120"))


def _utc_timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _result(ok, code, detail, **extra):
    payload = {"ok": ok, "code": code, "detail": detail}
    payload.update(extra)
    return payload


class RobotAuthManager:
    def __init__(self, user_file=None, timeout_sec=None):
        self._user_file = Path(user_file or os.environ.get("ROBOT_STATION_USERS_FILE", DEFAULT_USER_FILE))
        self._timeout_sec = float(timeout_sec if timeout_sec is not None else DEFAULT_TIMEOUT_SEC)
        self._lock = threading.RLock()
        self._users = {}
        self._users_mtime = None
        self._active = None
        self._revoked = {}

    # ---------------------------------------------------------------- users
    def _load_users_locked(self):
        try:
            stat = self._user_file.stat()
        except FileNotFoundError:
            self._users = {}
            self._users_mtime = None
            return
        if self._users_mtime == stat.st_mtime:
            return

        users = {}
        for raw_line in self._user_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                username, password = line.split(":", 1)
            else:
                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue
                username, password = parts
            username = username.strip()
            password = password.strip()
            if username:
                users[username] = password
        self._users = users
        self._users_mtime = stat.st_mtime

    def users(self):
        with self._lock:
            self._load_users_locked()
            return list(self._users.keys())

    # --------------------------------------------------------------- sessions
    def _clear_expired_locked(self):
        if not self._active:
            return None
        if self._timeout_sec <= 0:
            return None
        if time.monotonic() - self._active["lastSeenMono"] <= self._timeout_sec:
            return None
        expired = self._active
        self._active = None
        return expired

    def _remember_revoked_locked(self, session, reason, revoked_by=None):
        if not session:
            return
        self._revoked[session["token"]] = {
            "reason": reason,
            "revokedBy": revoked_by,
            "revokedAt": _utc_timestamp(),
            "user": session.get("user"),
        }
        while len(self._revoked) > 32:
            oldest = next(iter(self._revoked))
            self._revoked.pop(oldest, None)

    def _public_active_locked(self):
        if not self._active:
            return None
        return {
            "user": self._active["user"],
            "client": self._active.get("client", ""),
            "loginAt": self._active["loginAt"],
            "lastSeenAt": self._active["lastSeenAt"],
        }

    def status(self, token=None, touch=True):
        with self._lock:
            self._clear_expired_locked()
            if token and token in self._revoked:
                revoked = self._revoked[token]
                return _result(
                    False,
                    "AUTH-REVOKED",
                    "This operator session was revoked.",
                    authenticated=False,
                    revoked=True,
                    revokedBy=revoked.get("revokedBy"),
                    revokedAt=revoked.get("revokedAt"),
                    active=self._public_active_locked(),
                )
            if token and self._active and secrets.compare_digest(token, self._active["token"]):
                if touch:
                    self._active["lastSeenMono"] = time.monotonic()
                    self._active["lastSeenAt"] = _utc_timestamp()
                return _result(
                    True,
                    "AUTH-OK",
                    "Authenticated operator.",
                    authenticated=True,
                    user=self._active["user"],
                    active=self._public_active_locked(),
                    timeoutSec=self._timeout_sec,
                )
            return _result(
                False,
                "AUTH-REQUIRED",
                "Login required.",
                authenticated=False,
                active=self._public_active_locked(),
                users=self.users(),
                timeoutSec=self._timeout_sec,
            )

    def login(self, username, password, force=False, client=""):
        username = str(username or "").strip()
        password = str(password or "")
        with self._lock:
            self._load_users_locked()
            if username not in self._users or not secrets.compare_digest(password, self._users[username]):
                return _result(False, "AUTH-INVALID", "Invalid username or password.", authenticated=False), None

            self._clear_expired_locked()
            previous = self._active
            if previous and not force:
                return (
                    _result(
                        False,
                        "AUTH-CONFLICT",
                        "Another operator is already logged in.",
                        authenticated=False,
                        active=self._public_active_locked(),
                    ),
                    None,
                )

            if previous:
                self._remember_revoked_locked(previous, "forced_login", revoked_by=username)

            token = secrets.token_urlsafe(32)
            now = _utc_timestamp()
            self._active = {
                "token": token,
                "user": username,
                "client": str(client or ""),
                "loginAt": now,
                "lastSeenAt": now,
                "lastSeenMono": time.monotonic(),
            }
            code = "AUTH-FORCED" if previous else "AUTH-LOGIN"
            detail = "Operator session took over control." if previous else "Operator session started."
            return (
                _result(
                    True,
                    code,
                    detail,
                    authenticated=True,
                    user=username,
                    active=self._public_active_locked(),
                    revokedUser=previous.get("user") if previous else None,
                    timeoutSec=self._timeout_sec,
                ),
                token,
            )

    def logout(self, token=None):
        with self._lock:
            self._clear_expired_locked()
            if token and self._active and secrets.compare_digest(token, self._active["token"]):
                user = self._active["user"]
                self._active = None
                return _result(True, "AUTH-LOGOUT", "Operator session ended.", user=user, authenticated=False)
            return _result(True, "AUTH-LOGOUT", "No active matching operator session.", authenticated=False)

    def require_operator(self, token=None):
        status = self.status(token=token, touch=True)
        if status.get("authenticated"):
            return True, status
        return False, status


_manager = None
_manager_lock = threading.Lock()


def get_auth_manager():
    global _manager
    with _manager_lock:
        if _manager is None:
            _manager = RobotAuthManager()
        return _manager
