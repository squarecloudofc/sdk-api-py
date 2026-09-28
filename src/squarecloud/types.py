"""Response types. Every one is a ``TypedDict``: a plain ``dict`` at runtime,
so fields the API adds later never break the SDK. Field names mirror the API
(including its few camelCase keys such as ``lastModified`` and ``createdAt``).
"""

from typing import Any, Literal, NotRequired, TypedDict

DatabaseType = Literal['mongo', 'mysql', 'redis', 'postgres']
WorkspaceGroup = Literal['admin', 'maintain', 'manager', 'view']
SnapshotScope = Literal['applications', 'databases']
EnvVars = dict[str, str]


# Account / service ----------------------------------------------------------


class PlanMemory(TypedDict):
    limit: int
    available: int
    used: int


class Plan(TypedDict):
    name: str
    memory: PlanMemory
    duration: int | None


class User(TypedDict):
    id: str
    name: str
    email: str
    locale: str
    plan: Plan
    created_at: str


class AppSummary(TypedDict):
    id: str
    name: str
    desc: NotRequired[str]
    ram: int
    lang: str
    domain: NotRequired[str | None]  # left out when unset
    custom: NotRequired[str | None]
    cluster: str
    created_at: str


class DatabaseSummary(TypedDict):
    id: str
    name: str
    ram: int
    type: str
    cluster: str
    created_at: str


class Account(TypedDict):
    user: User
    applications: list[AppSummary]
    databases: list[DatabaseSummary]


class ServiceEntry(TypedDict):
    name: str
    status: str
    summary: NotRequired[str]
    unresolved_incidents: NotRequired[int]
    degraded_components: NotRequired[int]
    api_latency: NotRequired[dict[str, Any]]


class ServiceStatus(TypedDict):
    status: str  # 'online', 'degraded' or 'unknown'
    message: str
    checked_at: NotRequired[str]
    stale: NotRequired[bool]
    services: NotRequired[dict[str, ServiceEntry]]
    dependencies: NotRequired[dict[str, ServiceEntry]]


# AI -------------------------------------------------------------------------


class ChatMessage(TypedDict):
    role: Literal['system', 'user', 'assistant', 'tool']
    content: NotRequired[str]
    tool_call_id: NotRequired[str]
    tool_calls: NotRequired[list[dict[str, Any]]]


class ChatRequest(TypedDict):
    """The body of ``ai.chat``, sent as is: any other OpenAI parameter may
    be added (pass a plain ``dict`` to type-check it)."""

    messages: list[ChatMessage]
    model: NotRequired[str]
    max_tokens: NotRequired[int]
    temperature: NotRequired[float]
    tools: NotRequired[list[dict[str, Any]]]
    tool_choice: NotRequired[Literal['auto', 'none', 'required'] | dict[str, Any]]


class ChatChoice(TypedDict):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatUsage(TypedDict):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletion(TypedDict):
    id: str
    object: str
    created: int
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage


# Apps -----------------------------------------------------------------------


class AppLanguage(TypedDict):
    name: str
    version: str


class AppCreated(TypedDict):
    id: str
    name: str
    description: NotRequired[str]
    domain: NotRequired[str]  # the full <subdomain>.squareweb.app host of a website
    cluster: NotRequired[str]
    ram: int
    cpu: float
    language: AppLanguage


class App(TypedDict):
    id: str
    name: str
    desc: NotRequired[str]
    owner: str
    cluster: str
    ram: int
    language: str
    domain: NotRequired[str | None]  # left out when unset
    custom: NotRequired[str | None]
    created_at: str


class StatusListItem(TypedDict):
    id: str
    running: bool
    cpu: NotRequired[str]
    ram: NotRequired[str]


class StatsNetwork(TypedDict):
    total: str | list[int]
    now: str | list[int]


class RuntimeStats(TypedDict):
    """Formatted strings by default (``ram`` e.g. ``'120.4MB'``); ``cpu``
    and ``ram`` are numbers with ``raw=True``."""

    cpu: str | float
    ram: str | float
    status: str
    running: bool
    storage: str | int
    network: StatsNetwork
    uptime: int | None


class MetricPoint(TypedDict):
    """One 5-minute sample. ``metrics`` lists them newest first."""

    date: str
    cpu: float
    ram: float
    net: list[int]


class AppDomain(TypedDict):
    app_id: str
    hostname: str
    type: Literal['subdomain', 'custom']


class LoadBalancerApp(TypedDict):
    id: str
    name: str
    cluster: NotRequired[str]


class LoadBalancer(TypedDict):
    hostname: str
    apps: list[LoadBalancerApp]


class LoadBalancers(TypedDict):
    limit: int
    balancers: list[LoadBalancer]


class DeployFiles(TypedDict):
    added: list[str]
    removed: list[str]
    modified: list[str]


class DeployEvent(TypedDict):
    """``code`` and ``message`` explain a ``state='error'`` event."""

    id: str
    state: Literal['pending', 'clone', 'commit', 'restarting', 'success', 'error']
    date: str
    source: Literal['git']
    branch: NotRequired[str]
    code: NotRequired[str]
    message: NotRequired[str]
    files: NotRequired[DeployFiles]


class DeployRepository(TypedDict):
    id: int | None
    name: str | None
    branch: str | None


class LinkedRepository(TypedDict):
    """The repository ``deploys.link_github_app`` linked."""

    id: int
    full_name: str
    branch: str


class DeployCurrent(TypedDict):
    app: NotRequired[DeployRepository]
    webhook: NotRequired[str]


class FileEntry(TypedDict):
    name: str
    type: Literal['file', 'directory']
    size: NotRequired[int]  # omitted on some directory entries
    lastModified: NotRequired[float | None]  # Unix ms, may carry a fraction


# Snapshots ------------------------------------------------------------------


class Snapshot(TypedDict):
    """``restore`` takes ``name`` and ``version_id``; ``url`` is a signed
    download link (see ``download_snapshot``)."""

    name: str
    size: int
    modified: str
    key: str
    version_id: str
    url: str
    runtime: NotRequired[str | None]
    origin: NotRequired[Literal['automatic', 'manual'] | None]


class SnapshotCreated(TypedDict):
    """``pending=True`` (HTTP 202 ``SNAPSHOT_PROCESSING``) means the snapshot
    is still being generated: it appears in ``snapshots.list`` on its own,
    usually within 2 minutes. Poll ``list``; never call ``create`` again
    (one per 180 s per resource, and each call counts against the daily
    quota)."""

    pending: bool
    url: NotRequired[str]
    key: NotRequired[str]


# Network --------------------------------------------------------------------


class AnalyticsFilters(TypedDict, total=False):
    """The optional filters of ``network.analytics``, passed as keywords."""

    country: str  # 2-letter code, e.g. 'BR'
    ip: str
    path: str  # a prefix, e.g. '/api'
    status: str  # e.g. '404'
    os: str
    browser: str
    protocol: str
    referer: str  # 'Direct' means no referer
    provider: str  # 'NAME (ASN)', e.g. 'GOOGLE (15169)'
    content_type: str
    bot: str


class AnalyticsBucket(TypedDict):
    type: NotRequired[str]  # a provider is 'NAME (ASN)'
    visits: int
    requests: int
    bytes: int
    date: NotRequired[str]


class NetworkAnalytics(TypedDict, total=False):
    visits: list[AnalyticsBucket]
    countries: list[AnalyticsBucket]
    devices: list[AnalyticsBucket]
    os: list[AnalyticsBucket]
    browsers: list[AnalyticsBucket]
    protocols: list[AnalyticsBucket]
    methods: list[AnalyticsBucket]
    paths: list[AnalyticsBucket]
    referers: list[AnalyticsBucket]
    providers: list[AnalyticsBucket]
    ips: list[AnalyticsBucket]
    status_codes: list[AnalyticsBucket]
    bots: list[AnalyticsBucket]
    content_types: list[AnalyticsBucket]


class NetworkErrors(TypedDict, total=False):
    summary: dict[str, Any]
    by_status: list[dict[str, Any]]
    timeseries: list[dict[str, Any]]
    top_paths: list[dict[str, Any]]
    by_method: list[dict[str, Any]]


class NetworkLog(TypedDict):
    timestamp: str
    client: dict[str, Any]
    request: dict[str, Any]
    response: dict[str, Any]


class NetworkPerformance(TypedDict, total=False):
    summary: dict[str, Any]
    timeseries: list[dict[str, Any]]
    countries: list[dict[str, Any]]
    colos: list[dict[str, Any]]
    slowest_paths: list[dict[str, Any]]


class DNSRecord(TypedDict):
    type: Literal['txt', 'cname']
    name: str
    value: str
    status: str


# Realtime -------------------------------------------------------------------


class LogEvent(TypedDict):
    """A log line: ``line`` without its ``\\u0001``/``\\u0002`` prefix."""

    event: Literal['logs']
    data: str
    id: str | None
    stream: Literal['stdout', 'stderr']
    line: str


class IOCounter(TypedDict, total=False):
    i: float
    o: float


class NetIO(IOCounter, total=False):
    new: IOCounter  # bytes per second


class RealtimeStatus(TypedDict, total=False):
    """Live container metrics; lean frames are merged onto the last full
    one."""

    cpu: float
    cpuLimit: float  # CPU cores allocated
    ram: list[float]  # [used MB, limit MB]
    status: str
    netIO: NetIO
    bIO: IOCounter
    uptime: int  # Unix ms of the container start


class StatusEvent(TypedDict):
    """``status`` is the full status (lean frames merged onto the last full
    one); ``data`` is the raw frame."""

    event: Literal['status']
    data: str
    id: str | None
    status: RealtimeStatus


class SystemEvent(TypedDict):
    """``data`` is the code, e.g. ``'REALTIME_CONNECTING | <id>'``,
    ``'REALTIME_DISCONNECTED'`` or ``'CONTAINER_NOT_FOUND'``. A frame with
    no ``event:`` line is a ``'message'``; an event type the API adds later
    passes through in this shape."""

    event: Literal['system', 'error', 'message']
    data: str
    id: str | None


RealtimeEvent = LogEvent | StatusEvent | SystemEvent
"""One SSE event, discriminated on ``event``; ``data`` is always the raw
text."""


# Databases ------------------------------------------------------------------


class DatabaseCreated(TypedDict):
    id: str
    name: str
    memory: int
    cpu: float
    type: DatabaseType
    password: str
    certificate: NotRequired[str | None]
    connection_url: str
    cluster: str


class Database(TypedDict):
    id: str
    name: str
    owner: str
    cluster: str
    ram: int
    type: DatabaseType
    port: int
    created_at: str


# Workspaces -----------------------------------------------------------------


class WorkspaceMember(TypedDict):
    id: str
    name: str | None
    group: Literal['owner', 'admin', 'maintain', 'manager', 'view']
    joinedAt: str


class WorkspaceApp(TypedDict):
    """``id`` is the raw app id. To act on it, use ``f'{id}-{workspace_id}'``."""

    id: str
    name: str
    desc: str | None
    ram: int
    lang: str
    domain: NotRequired[str | None]  # left out when unset
    custom: NotRequired[str | None]


class Workspace(TypedDict):
    id: str  # 32 hex (a hyphenless uuid) or 40 hex
    name: str
    owner: str
    members: list[WorkspaceMember]
    applications: list[WorkspaceApp]
    createdAt: str


class WorkspaceCreated(TypedDict):
    id: str
    name: str
