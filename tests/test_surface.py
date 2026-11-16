"""The public names import from both ``squarecloud`` and ``squarecloud.client``
(the client was one module before it was split)."""

from __future__ import annotations

import importlib

import squarecloud
import squarecloud.client

PUBLIC = [
    'BASE_URL',
    'AsyncRealtime',
    'AsyncSquareCloud',
    'HTTPTransport',
    'Realtime',
    'Response',
    'SquareCloud',
    'SquareCloudAPIError',
    'Transport',
    '__version__',
    'types',
]

# Importable from the single-module ``squarecloud.client`` of v5.0 (it had no
# ``__all__``): kept there for compatibility, outside ``__all__``.
LEGACY = [
    'USER_AGENT',
    'MAX_UPLOAD_BYTES',
    'MAX_FILE_BYTES',
    'UploadFile',
    'Time',
    'Body',
    *(
        prefix + name
        for prefix in ('', 'Async')
        for name in (
            'Account',
            'Service',
            'AI',
            'Apps',
            'Deploys',
            'Envs',
            'Files',
            'Network',
            'Snapshots',
            'Databases',
            'Workspaces',
            'Members',
            'WorkspaceApps',
        )
    ),
]


def test_public_imports() -> None:
    assert sorted(squarecloud.__all__) == sorted(PUBLIC)
    assert sorted(squarecloud.client.__all__) == sorted(PUBLIC)
    for name in PUBLIC:
        assert getattr(squarecloud.client, name) is getattr(squarecloud, name), name


def test_legacy_client_imports() -> None:
    module = importlib.import_module('squarecloud.client')
    missing = [name for name in LEGACY if not hasattr(module, name)]
    assert missing == []
    assert not set(LEGACY) & set(squarecloud.client.__all__)
