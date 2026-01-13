import sys


def _patch_testclient_allow_redirects() -> None:
    if "pytest" not in sys.modules:
        return

    try:
        from fastapi.testclient import TestClient
    except Exception:
        return

    if getattr(TestClient.post, "_allow_redirects_compat", False):
        return

    original_post = TestClient.post

    def post(self, url, **kwargs):
        if "allow_redirects" in kwargs and "follow_redirects" not in kwargs:
            kwargs["follow_redirects"] = kwargs.pop("allow_redirects")
        return original_post(self, url, **kwargs)

    post._allow_redirects_compat = True
    TestClient.post = post


_patch_testclient_allow_redirects()
