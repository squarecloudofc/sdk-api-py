"""Spec conformance: every public operation against the pinned
``spec/openapi.json`` through a mock transport."""

from __future__ import annotations

import base64
import json
import re
import types
import typing
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, get_args, get_origin, is_typeddict

import pytest
from helpers import APP, DB, KEY, WS, Call, FakeResponse, MockTransport, multipart

from squarecloud import AsyncSquareCloud, SquareCloud, SquareCloudAPIError

SPEC = json.loads(
    (Path(__file__).parents[1] / 'spec' / 'openapi.json').read_text('utf-8')
)
GROUPS = ('account', 'service', 'ai', 'apps', 'databases', 'workspaces')
NOT_FOR_SDKS = {('GET', '/v2/openapi.json'), ('POST', '/v2/git/webhook/{webhook}')}
OPS = {
    (method.upper(), path)
    for path, item in SPEC['paths'].items()
    for method in item
    if method in {'get', 'post', 'put', 'patch', 'delete'}
} - NOT_FOR_SDKS
START, END = '2026-09-01T00:00:00Z', '2026-09-02T00:00:00Z'
ZIP = b'PK\x03\x04zip'
VID = '3/L4kqtJlc+rmSpX==abcdefghij'  # an S3-style version id
MEMBER = '1234567890'
PROVIDER = 'GOOGLE (15169)'  # 'NAME (ASN)', as analytics reports it
MSG = [{'role': 'user', 'content': 'hi'}]

# (sdk method, args, kwargs). Covers every public operation once, with every
# optional parameter set so its wire name is checked too.
CASES: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = [
    ('account.me', (), {}),
    ('account.snapshots', (), {'scope': 'databases'}),
    ('service.status', (), {}),
    (
        'ai.chat',
        (
            {
                'model': 'cubic',
                'messages': MSG,
                'max_tokens': 5,
                'temperature': 0.2,
                'tools': [],
                'tool_choice': 'auto',
            },
        ),
        {},
    ),
    ('apps.create', (ZIP,), {}),
    ('apps.get', (APP,), {}),
    ('apps.delete', (APP,), {}),
    ('apps.status_all', (), {'workspace_id': WS}),
    ('apps.status', (APP,), {'raw': True}),
    ('apps.start', (APP,), {}),
    ('apps.stop', (APP,), {}),
    ('apps.restart', (APP,), {}),
    ('apps.logs', (APP,), {}),
    ('apps.metrics', (APP,), {}),
    ('apps.realtime', (APP,), {}),
    ('apps.domains', (), {}),
    ('apps.load_balancers', (), {}),
    ('apps.commit', (APP, ZIP), {'path': '/src'}),
    ('apps.deploys.set_webhook', (APP, 'ghp_token'), {}),
    ('apps.deploys.link_github_app', (APP, 'octocat/hello-world', 'main'), {}),
    ('apps.deploys.unlink_github_app', (APP,), {}),
    ('apps.deploys.list', (APP,), {}),
    ('apps.deploys.current', (APP,), {}),
    ('apps.envs.get', (APP,), {}),
    ('apps.envs.set', (APP, {'A': '1'}), {}),
    ('apps.envs.replace', (APP, {'A': '1'}), {}),
    ('apps.envs.delete', (APP, ['A']), {}),
    ('apps.files.list', (APP, '/src'), {}),
    ('apps.files.read', (APP, '/src/index.js'), {}),
    ('apps.files.write', (APP, '/src/index.js', 'console.log(1)'), {}),
    ('apps.files.move', (APP, '/a.js', '/b.js'), {}),
    ('apps.files.delete', (APP, '/a.js'), {}),
    ('apps.snapshots.list', (APP,), {}),
    ('apps.snapshots.create', (APP,), {}),
    ('apps.snapshots.restore', (APP, 'abc123_javascript_manual', VID), {}),
    (
        'apps.network.analytics',
        (APP, START, END),
        {
            'country': 'BR',
            'ip': '203.0.113.1',
            'path': '/api',
            'status': '404',
            'os': 'Linux',
            'browser': 'Chrome',
            'protocol': 'HTTP/2',
            'referer': 'x.com',
            'provider': PROVIDER,
            'content_type': 'text/html',
            'bot': 'none',
        },
    ),
    ('apps.network.errors', (APP, START, END), {'include_4xx': True}),
    ('apps.network.logs', (APP, START, END), {}),
    ('apps.network.performance', (APP, START, END), {}),
    ('apps.network.dns', (APP,), {}),
    ('apps.network.set_domain', (APP, 'example.com'), {}),
    ('apps.network.purge_cache', (APP,), {}),
    (
        'databases.create',
        ('db',),
        {'type': 'postgres', 'version': '17', 'memory': 512},
    ),
    ('databases.get', (DB,), {}),
    ('databases.update', (DB,), {'name': 'db2', 'ram': 1024}),
    ('databases.delete', (DB,), {}),
    ('databases.start', (DB,), {}),
    ('databases.stop', (DB,), {}),
    ('databases.status', (DB,), {'raw': True}),
    ('databases.metrics', (DB,), {}),
    ('databases.status_all', (), {}),
    ('databases.certificate', (DB,), {}),
    ('databases.reset_credentials', (DB, 'password'), {}),
    ('databases.snapshots.list', (DB,), {}),
    ('databases.snapshots.create', (DB,), {}),
    ('databases.snapshots.restore', (DB, 'abc123_mongo', VID), {}),
    ('workspaces.create', ('Acme',), {}),
    ('workspaces.list', (), {}),
    ('workspaces.get', (WS,), {}),
    ('workspaces.delete', (WS,), {}),
    ('workspaces.leave', (WS,), {}),
    ('workspaces.members.add', (WS, 'invite-code', 'view'), {}),
    ('workspaces.members.update', (WS, MEMBER, 'admin'), {}),
    ('workspaces.members.remove', (WS, MEMBER), {}),
    ('workspaces.members.invite_code', (), {}),
    ('workspaces.apps.add', (WS, APP), {}),
    ('workspaces.apps.remove', (WS, APP), {}),
]

# The exact JSON body of every case that sends one: catches swapped values
# that a key-only check would miss.
BODIES: dict[str, Any] = {
    'ai.chat': {
        'model': 'cubic',
        'messages': MSG,
        'max_tokens': 5,
        'temperature': 0.2,
        'tools': [],
        'tool_choice': 'auto',
    },
    'apps.deploys.set_webhook': {'access_token': 'ghp_token'},
    'apps.deploys.link_github_app': {
        'repositoryName': 'octocat/hello-world',
        'repositoryBranch': 'main',
    },
    'apps.envs.set': {'envs': {'A': '1'}},
    'apps.envs.replace': {'envs': {'A': '1'}},
    'apps.envs.delete': {'envs': ['A']},
    'apps.files.write': {'path': '/src/index.js', 'content': 'console.log(1)'},
    'apps.files.move': {'path': '/a.js', 'to': '/b.js'},
    'apps.files.delete': {'path': '/a.js'},
    'apps.snapshots.restore': {
        'snapshotId': 'abc123_javascript_manual',
        'versionId': VID,
    },
    'apps.network.set_domain': {'custom': 'example.com'},
    'databases.create': {
        'name': 'db',
        'type': 'postgres',
        'version': '17',
        'memory': 512,
    },
    'databases.update': {'name': 'db2', 'ram': 1024},
    'databases.reset_credentials': {'reset': 'password'},
    'databases.snapshots.restore': {'snapshotId': 'abc123_mongo', 'versionId': VID},
    'workspaces.create': {'name': 'Acme'},
    'workspaces.delete': {'workspaceId': WS},
    'workspaces.leave': {'workspaceId': WS},
    'workspaces.members.add': {
        'workspaceId': WS,
        'code': 'invite-code',
        'group': 'view',
    },
    'workspaces.members.update': {
        'workspaceId': WS,
        'memberId': MEMBER,
        'group': 'admin',
    },
    'workspaces.members.remove': {'workspaceId': WS, 'memberId': MEMBER},
    'workspaces.apps.add': {'workspaceId': WS, 'appId': APP},
    'workspaces.apps.remove': {'workspaceId': WS, 'appId': APP},
}

# The exact query of every case that sends one: catches a swapped or
# hard-coded value that the schema check would accept.
RAW = {'rawData': 'true'}
WINDOW = {'start': START, 'end': END}
QUERIES: dict[str, dict[str, str]] = {
    'account.snapshots': {'scope': 'databases'},
    'apps.status_all': {'workspaceId': WS},
    'apps.status': RAW,
    'apps.commit': {'path': '/src'},
    'apps.files.list': {'path': '/src'},
    'apps.files.read': {'path': '/src/index.js', 'encoding': 'base64'},
    'apps.network.analytics': {
        **WINDOW,
        'country': 'BR',
        'ip': '203.0.113.1',
        'path': '/api',
        'status': '404',
        'os': 'Linux',
        'browser': 'Chrome',
        'protocol': 'HTTP/2',
        'referer': 'x.com',
        'provider': PROVIDER,
        'content_type': 'text/html',
        'bot': 'none',
    },
    'apps.network.errors': {**WINDOW, 'include_4xx': 'true'},
    'apps.network.logs': WINDOW,
    'apps.network.performance': WINDOW,
    'databases.status': RAW,
}


def resolve(node: Any) -> Any:
    while isinstance(node, dict) and '$ref' in node:
        target: Any = SPEC
        for part in node['$ref'].split('/')[1:]:
            target = target[part]
        node = target
    return node


def template_of(method: str, path: str) -> str:
    """The spec path matching ``path``; literal segments win over params."""
    candidates = sorted(SPEC['paths'], key=lambda p: p.count('{'))
    for template in candidates:
        pattern = re.sub(r'\\\{[^/]+?\\\}', '[^/]+', re.escape(template))
        if re.fullmatch(pattern, path) and method.lower() in SPEC['paths'][template]:
            return template
    raise AssertionError(f'{method} {path} is not in the spec')


def operation(method: str, template: str) -> Any:
    return SPEC['paths'][template][method.lower()]


def examples(media: dict[str, Any]) -> list[Any]:
    if 'example' in media:
        return [media['example']]
    return [v['value'] for v in (media.get('examples') or {}).values()]


def success_bodies(op: Any, status: str = '200') -> list[Any]:
    """Every example of a success response (each one is exercised)."""
    media = resolve(op['responses'][status])['content']
    [(content_type, body)] = media.items()
    values = examples(body)
    assert values, 'every SDK operation has a success example'
    if content_type == 'text/event-stream':
        return [v.encode() for v in values]
    return values


PYTHON_TYPES: dict[str, Any] = {
    'string': str,
    'integer': int,
    'number': (int, float),
    'boolean': bool,
    'array': list,
    'object': dict,
}


def check_value(value: Any, schema: Any, where: str) -> None:
    """The JSON-schema subset the spec uses for request values."""
    schema = resolve(schema)
    if 'oneOf' in schema:
        errors = []
        for option in schema['oneOf']:
            try:
                return check_value(value, option, where)
            except AssertionError as exc:
                errors.append(exc)
        raise AssertionError(f'{where}: {value!r} matches no oneOf: {errors}')
    kind = schema.get('type')
    if kind:
        assert isinstance(value, PYTHON_TYPES[kind]), f'{where}: {value!r} not {kind}'
        assert kind == 'boolean' or not isinstance(value, bool), where
    if 'enum' in schema:
        assert value in schema['enum'], f'{where}: {value!r} not in the enum'
    if 'pattern' in schema:
        assert re.search(schema['pattern'], value), f'{where}: {value!r} !~ pattern'
    if kind == 'array' and 'items' in schema:
        for i, item in enumerate(value):
            check_value(item, schema['items'], f'{where}[{i}]')
    if kind == 'object' and isinstance(schema.get('additionalProperties'), dict):
        for k, v in value.items():
            check_value(v, schema['additionalProperties'], f'{where}.{k}')


def check_request(call: Call) -> tuple[str, str]:
    template = template_of(call.method, call.path)
    key = (call.method, template)
    assert key in OPS, key
    op = operation(call.method, template)
    params = [resolve(p) for p in op.get('parameters', [])]
    declared = {p['name']: p for p in params if p['in'] == 'query'}
    required = {p['name'] for p in params if p['in'] == 'query' and p.get('required')}
    assert set(call.query) <= set(declared), (key, set(call.query) - set(declared))
    assert required <= set(call.query), (key, required - set(call.query))
    for name, [value] in call.query.items():
        check_value(value, declared[name].get('schema', {}), f'{key} ?{name}')
    body = resolve(op.get('requestBody', {})).get('content', {})
    if 'application/json' in body:
        schema = resolve(body['application/json']['schema'])
        sent = call.json()
        assert call.headers['Content-Type'] == 'application/json'
        assert set(sent) <= set(schema['properties']), (
            key,
            set(sent) - set(schema['properties']),
        )
        assert set(schema.get('required', [])) <= set(sent), key
        for name, value in sent.items():
            check_value(value, schema['properties'][name], f'{key} {name}')
    elif 'multipart/form-data' in body:
        names = {
            name
            for name, _, _ in multipart(call.body or b'', call.headers['Content-Type'])
        }
        assert names == set(resolve(body['multipart/form-data']['schema'])['required'])
    else:
        assert call.body is None, key
    return key


def conforms(value: Any, tp: Any, where: str = '$') -> None:
    """A small runtime check of a value against a type annotation."""
    origin, args = get_origin(tp), get_args(tp)
    if tp is Any:
        return
    if tp is None or tp is type(None):
        assert value is None, where
    elif origin in (typing.Union, types.UnionType):
        errors = []
        for option in args:
            try:
                return conforms(value, option, where)
            except AssertionError as exc:
                errors.append(exc)
        raise AssertionError(f'{where}: {value!r} matches none of {tp}: {errors}')
    elif origin is Literal:
        assert value in args, f'{where}: {value!r} not in {args}'
    elif origin is list:
        assert isinstance(value, list), where
        for i, item in enumerate(value):
            conforms(item, args[0], f'{where}[{i}]')
    elif origin is dict:
        assert isinstance(value, dict), where
        for k, v in value.items():
            conforms(v, args[1], f'{where}.{k}')
    elif is_typeddict(tp):
        assert isinstance(value, dict), f'{where}: {value!r} is not a dict'
        missing = tp.__required_keys__ - value.keys()
        assert not missing, f'{where}: missing {missing}'
        hints = typing.get_type_hints(tp)
        extra = value.keys() - hints.keys()
        assert not extra, f'{where}: keys the type does not declare: {extra}'
        for k in value.keys() & hints.keys():
            conforms(value[k], hints[k], f'{where}.{k}')
    elif tp is float:
        assert isinstance(value, int | float) and not isinstance(value, bool), where
    elif tp is int:
        assert isinstance(value, int) and not isinstance(value, bool), where
    else:
        assert isinstance(value, tp), f'{where}: {value!r} is not {tp}'


def target(client: SquareCloud, dotted: str) -> Callable[..., Any]:
    obj: Any = client
    for part in dotted.split('.'):
        obj = getattr(obj, part)
    return typing.cast(Callable[..., Any], obj)


def run(fn: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    result = fn(*args, **kwargs)
    return list(result) if type(result).__name__ == 'Realtime' else result


def return_type(client: SquareCloud, dotted: str) -> Any:
    fn = target(client, dotted)
    if dotted == 'apps.realtime':
        from squarecloud.types import RealtimeEvent

        return list[RealtimeEvent]
    return typing.get_type_hints(fn)['return']


def spec_client(index: int = 0) -> tuple[SquareCloud, MockTransport]:
    """A client answered by the ``index``-th success example (or the last)."""

    def answer(call: Call) -> FakeResponse:
        op = operation(call.method, template_of(call.method, call.path))
        bodies = success_bodies(op)
        return FakeResponse(200, bodies[min(index, len(bodies) - 1)])

    transport = MockTransport(handler=answer)
    return SquareCloud(KEY, transport=transport), transport


def check_scalar(result: Any, body: Any) -> None:
    """A method that unwraps one value must return the example's value."""
    response = body.get('response') if isinstance(body, dict) else None
    if not isinstance(response, dict):  # e.g. a webhook removal: no value
        assert not result, result
    elif isinstance(result, bytes):
        assert result == base64.b64decode(response['data'])
    else:
        assert result, f'{result!r} is empty but the example has {response}'
        assert result in response.values(), (result, response)


@pytest.mark.parametrize(('name', 'args', 'kwargs'), CASES, ids=[c[0] for c in CASES])
def test_operation_matches_spec(
    name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> None:
    client, transport = spec_client()
    run(target(client, name), args, kwargs)
    [call] = transport.calls
    method, template = check_request(call)
    if name in BODIES:
        assert call.json() == BODIES[name]
    assert {k: v[0] for k, v in call.query.items()} == QUERIES.get(name, {})
    tp = return_type(client, name)
    for i, body in enumerate(success_bodies(operation(method, template))):
        result = run(target(spec_client(i)[0], name), args, kwargs)
        conforms(result, tp, f'{name}[example {i}]')
        if tp in (str, bytes, str | None):
            check_scalar(result, body)


def test_every_json_body_is_pinned() -> None:
    client, transport = spec_client()
    for name, args, kwargs in CASES:
        run(target(client, name), args, kwargs)
        call = transport.calls[-1]
        is_json = call.headers.get('Content-Type') == 'application/json'
        assert is_json == (name in BODIES), name


def test_every_sdk_relevant_operation_is_covered() -> None:
    client, transport = spec_client()
    for name, args, kwargs in CASES:
        run(target(client, name), args, kwargs)
    covered = {check_request(call) for call in transport.calls}
    assert SPEC['info']['version'] == '13.76.1'
    assert len(OPS) == 67
    assert covered == OPS, (OPS - covered, covered - OPS)
    assert len(CASES) == 67


def test_every_spec_error_code_is_known() -> None:
    """The known-code list in the error docstring covers the spec enum."""
    known = set(re.findall(r'\b[A-Z][A-Z0-9_]+\b', SquareCloudAPIError.__doc__ or ''))
    spec = set(SPEC['components']['schemas']['ErrorCode']['enum'])
    assert len(spec) == 131
    # Listed in the enum, but only an internal (non-public) route sends them.
    internal = {'SUBDOMAIN_TAKEN', 'DEPLOY_FAILED'}
    assert not internal & known
    spec -= internal
    assert not spec - known, sorted(spec - known)
    assert 'APIKEY_EXPIRED' not in known


def surface(group: Any, prefix: str) -> set[str]:
    """The public methods of a group and of its nested groups."""
    names: set[str] = set()
    for name in dir(group):
        if not name.startswith('_'):
            value = getattr(group, name)
            if callable(value):
                names.add(prefix + name)
            else:
                names |= surface(value, f'{prefix}{name}.')
    return names


@pytest.mark.parametrize('cls', [SquareCloud, AsyncSquareCloud])
def test_public_methods_are_exactly_the_operations(cls: Any) -> None:
    client = cls(KEY, transport=MockTransport())
    found = set().union(*(surface(getattr(client, g), f'{g}.') for g in GROUPS))
    assert found == {name for name, _, _ in CASES}
    public = {n for n in dir(client) if not n.startswith('_')}
    assert public == {*GROUPS, 'close', 'download_snapshot'}


@pytest.mark.parametrize(
    'name', ['apps.snapshots.create', 'databases.snapshots.create']
)
def test_spec_202_example_is_pending(name: str) -> None:
    client, _ = spec_client()
    prefix = (
        '/v2/apps/{appId}' if name.startswith('apps') else '/v2/databases/{databaseId}'
    )
    [body] = success_bodies(operation('POST', prefix + '/snapshots'), '202')
    client._transport = MockTransport([FakeResponse(202, body)])
    assert target(client, name)(APP) == {'pending': True}


def error_examples() -> list[tuple[str, int, Any]]:
    """Every documented error example, paired with a case that hits it."""
    by_op: dict[tuple[str, str], str] = {}
    client, transport = spec_client()
    for name, args, kwargs in CASES:
        run(target(client, name), args, kwargs)
        by_op.setdefault(check_request(transport.calls[-1]), name)
    found = []
    for (method, template), name in sorted(by_op.items()):
        for status, response in operation(method, template)['responses'].items():
            if status.startswith('2'):
                continue
            for media in resolve(response).get('content', {}).values():
                values = examples(media)
                found += [(name, int(status), v) for v in values if isinstance(v, dict)]
    return found


@pytest.mark.parametrize(('name', 'status', 'body'), error_examples())
def test_spec_error_examples_raise_with_their_code(
    name: str, status: int, body: Any
) -> None:
    args, kwargs = next((a, k) for n, a, k in CASES if n == name)
    client = SquareCloud(
        KEY,
        transport=MockTransport(handler=lambda _: FakeResponse(status, body)),
        max_retries=0,
    )
    with pytest.raises(SquareCloudAPIError) as info:
        run(target(client, name), args, kwargs)
    expected = (
        body['error']['code']
        if isinstance(body.get('error'), dict)
        else body.get('code', 'UNKNOWN_ERROR')
    )
    assert (info.value.status, info.value.code) == (status, expected)


# Responses the live suite saw that the spec examples do not show. Each must
# decode into the SDK's return type (regression for the types it loosened).
_APP = {'id': APP, 'name': 'web', 'ram': 512, 'lang': 'javascript'}
LIVE_BODIES: list[tuple[str, Any]] = [
    # POST /apps: `domain` is the full host of a website
    (
        'apps.create',
        {
            'id': APP,
            'name': 'web',
            'domain': 'web.squareweb.app',
            'ram': 512,
            'cpu': 0.5,
            'language': {'name': 'javascript', 'version': 'recommended'},
            'cluster': 'example-cluster',
        },
    ),
    # `custom` (and `domain`, off a website) is left out when unset
    (
        'apps.get',
        {
            'id': APP,
            'name': 'bot',
            'owner': '1',
            'cluster': 'example-cluster',
            'ram': 256,
            'language': 'javascript',
            'created_at': '2026-09-27T00:00:00.000Z',
        },
    ),
    (
        'account.me',
        {
            'user': {
                'id': '1',
                'name': 'n',
                'email': 'e',
                'locale': 'en',
                'plan': {
                    'name': 'pro-12',
                    'memory': {'limit': 12288, 'available': 11776, 'used': 512},
                    'duration': None,
                },
                'created_at': '2026-09-27T00:00:00.000Z',
            },
            'applications': [
                {
                    **_APP,
                    'domain': 'web.squareweb.app',
                    'cluster': 'example-cluster',
                    'created_at': '2026-09-27T00:00:00.000Z',
                }
            ],
            'databases': [],
        },
    ),
    (
        'workspaces.get',
        {
            'id': WS,
            'name': 'ws',
            'owner': '1',
            'members': [
                {'id': '1', 'name': 'n', 'group': 'owner', 'joinedAt': '2026-09-27'}
            ],
            'applications': [{**_APP, 'desc': None, 'domain': 'web.squareweb.app'}],
            'createdAt': '2026-09-27T00:00:00.000Z',
        },
    ),
    # `lastModified` is fs mtimeMs (it carries a fraction); a directory entry
    # (e.g. one a commit just unpacked) may come without `size` and `lastModified`
    (
        'apps.files.list',
        [
            {
                'type': 'file',
                'name': 'index.js',
                'size': 120,
                'lastModified': 1790518259302.0295,
            },
            {'type': 'directory', 'name': 'node_modules'},
        ],
    ),
]


@pytest.mark.parametrize(('name', 'response'), LIVE_BODIES)
def test_live_responses_fit_the_types(name: str, response: Any) -> None:
    client = SquareCloud(
        KEY,
        transport=MockTransport(
            handler=lambda _: FakeResponse(
                200, {'status': 'success', 'response': response}
            )
        ),
    )
    args, kwargs = next((a, k) for n, a, k in CASES if n == name)
    result = run(target(client, name), args, kwargs)
    assert result == response
    conforms(result, return_type(client, name))
