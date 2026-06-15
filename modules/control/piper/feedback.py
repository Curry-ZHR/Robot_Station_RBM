import os


DEFAULT_LEFT_JOINT_STATE_KEYS = ("piper_left_joint_state_double", "piper_left_joint_state")
DEFAULT_RIGHT_JOINT_STATE_KEYS = ("piper_right_joint_state_double", "piper_right_joint_state")


class PiperJointFeedbackError(RuntimeError):
    pass


def _split_key_list(raw):
    if raw is None:
        return []
    return [item.strip() for item in str(raw).split(",") if item.strip()]


def _dedupe(values):
    out = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return tuple(out)


def joint_state_key_candidates(side, list_env=None, single_env=None):
    defaults = DEFAULT_LEFT_JOINT_STATE_KEYS if side == "left" else DEFAULT_RIGHT_JOINT_STATE_KEYS
    if list_env and os.environ.get(list_env) is not None:
        keys = _split_key_list(os.environ.get(list_env))
    else:
        keys = _split_key_list(os.environ.get(single_env)) if single_env else []
        keys.extend(defaults)
    return _dedupe(keys) or defaults


def read_joint_state_candidate(reader, side, keys, timeout_sec=0.0, min_positions=7, accept_stale=True):
    errors = []
    stale_match = None
    for key in keys:
        try:
            result = reader.read(key, timeout_sec=timeout_sec)
        except Exception as exc:
            errors.append(f"{key}: {exc}")
            continue

        if not result.get("ok"):
            errors.append(f"{key}: {result.get('detail', 'no data')}")
            continue

        data = result.get("data") or {}
        positions = data.get("position")
        if not isinstance(positions, (list, tuple)) or len(positions) < min_positions:
            errors.append(f"{key}: expected at least {min_positions} positions")
            continue

        if result.get("stale"):
            errors.append(f"{key}: stale")
            if stale_match is None:
                stale_match = (key, result, positions)
            continue

        return key, result, positions

    if accept_stale and stale_match is not None:
        return stale_match

    joined_keys = ", ".join(keys)
    joined_errors = "; ".join(errors) if errors else "no candidates configured"
    raise PiperJointFeedbackError(f"{side} joint state unavailable from {joined_keys}: {joined_errors}")
