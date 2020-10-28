from digirent.api.scopes import is_allowed


def test_permission_granted_when_read_required_but_user_is_only_permitted_write():
    assert is_allowed("user:read", ["user:write", "items:read"])


def test_permission_denied_when_write_required_but_user_is_only_permitted_read():
    assert not is_allowed("user:write", ["user:read", "items:write"])


def test_permission_granted_when_read_required_and_user_only_has_read_permission():
    assert is_allowed("user:read", ["user:read", "items:write"])


def test_permission_is_denied_when_user_lacks_required_permission():
    assert not is_allowed("user:read", ["items:read", "items:write"])
