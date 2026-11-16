"""Types of the values that the API returns and accepts.

Every type is a ``TypedDict``, so at runtime it is a plain ``dict`` that
keeps any field the API adds later. Field names are the API's own,
including its few camelCase keys such as ``lastModified`` and ``createdAt``.
"""

from typing import Any, Literal, NotRequired, TypedDict

DatabaseType = Literal['mongo', 'mysql', 'redis', 'postgres']
WorkspaceGroup = Literal['admin', 'maintain', 'manager', 'view']
SnapshotScope = Literal['applications', 'databases']
EnvVars = dict[str, str]


# Account / service ----------------------------------------------------------


class PlanMemory(TypedDict):
    """Your plan's memory, in MB, across all applications and databases."""

    limit: int  # The plan's total memory.
    available: int  # Memory not allocated yet.
    used: int  # Memory allocated to applications and databases.


class Plan(TypedDict):
    """The plan of your account."""

    name: str  # Such as 'standard-8'. 'free' means no active plan.
    memory: PlanMemory
    # Unix ms when the plan expires, or None without an active plan.
    duration: int | None


class User(TypedDict):
    """Your user profile."""

    id: str
    name: str
    email: str
    locale: str  # Such as 'en-US'.
    plan: Plan
    created_at: str


class AppSummary(TypedDict):
    """An application as listed in :class:`Account`."""

    id: str
    name: str
    desc: NotRequired[str]  # Left out when unset.
    ram: int  # Memory in MB.
    lang: str  # The language, such as 'python'.
    domain: NotRequired[str | None]  # The default subdomain host, left out when unset.
    custom: NotRequired[str | None]  # The custom domain, left out when unset.
    cluster: str
    created_at: str


class DatabaseSummary(TypedDict):
    """A database as listed in :class:`Account`."""

    id: str
    name: str
    ram: int  # Memory in MB.
    type: str  # The engine, such as 'postgres'.
    cluster: str
    created_at: str


class Account(TypedDict):
    """Your profile with the applications and databases you own."""

    user: User
    applications: list[AppSummary]
    databases: list[DatabaseSummary]


class ServiceEntry(TypedDict):
    """The health of one Square Cloud service or external dependency."""

    name: str
    status: str  # 'operational', 'degraded', 'outage', 'maintenance' or 'unknown'.
    summary: NotRequired[str]  # What is wrong, present only when not operational.
    unresolved_incidents: NotRequired[int]
    degraded_components: NotRequired[int]
    api_latency: NotRequired[dict[str, Any]]


class ServiceIncident(TypedDict):
    """A maintenance window or an incident from the status page."""

    type: Literal['maintenance', 'incident']
    title: str
    status: Literal['maintenance', 'degraded', 'outage', 'operational', 'unknown']
    started_at: str
    ends_at: NotRequired[str | None]  # The expected end, or None when not announced.
    affected: list[str]  # The names of the affected components.
    update: NotRequired[str]  # The latest update, which may use Markdown.
    updated_at: NotRequired[str | None]


class ServiceComponent(TypedDict):
    """A status page component that is not operational."""

    name: str
    status: Literal['maintenance', 'degraded', 'outage']


class ServiceStatus(TypedDict):
    """The status of Square Cloud and of the services it depends on."""

    # 'online', 'maintenance', 'degraded' or 'unknown'. 'unknown' means the check itself
    # could not run, which is not an outage.
    status: str
    message: str
    checked_at: NotRequired[str]
    # True when the status was checked live because the regular report was unavailable.
    stale: NotRequired[bool]
    services: NotRequired[dict[str, ServiceEntry]]  # Square Cloud's own services.
    # The external services Square Cloud depends on.
    dependencies: NotRequired[dict[str, ServiceEntry]]
    # Open maintenance windows and incidents, newest first.
    incidents: NotRequired[list[ServiceIncident]]
    # Status page components that are not operational.
    components: NotRequired[list[ServiceComponent]]


# AI -------------------------------------------------------------------------


class ChatMessage(TypedDict):
    """One message of a chat conversation."""

    role: Literal['system', 'user', 'assistant', 'tool']
    content: NotRequired[str]
    tool_call_id: NotRequired[str]
    tool_calls: NotRequired[list[dict[str, Any]]]


class ChatRequest(TypedDict):
    """The body of ``ai.chat``, sent as is, so you can add any OpenAI parameter."""

    messages: list[ChatMessage]
    model: NotRequired[str]
    max_tokens: NotRequired[int]
    max_completion_tokens: NotRequired[int]  # Takes precedence over max_tokens.
    temperature: NotRequired[float]
    tools: NotRequired[list[dict[str, Any]]]
    tool_choice: NotRequired[Literal['auto', 'none', 'required'] | dict[str, Any]]


class ChatChoice(TypedDict):
    """One reply of a chat completion."""

    index: int
    message: ChatMessage
    finish_reason: str


class ChatUsage(TypedDict):
    """The tokens a chat completion used."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletion(TypedDict):
    """The reply of ``ai.chat``, in the OpenAI format."""

    id: str
    object: str
    created: int  # Unix seconds.
    model: str
    choices: list[ChatChoice]
    usage: ChatUsage


# Apps -----------------------------------------------------------------------


class AppLanguage(TypedDict):
    """The detected language of a new application."""

    name: str
    version: str


class AppCreated(TypedDict):
    """The application that ``apps.create`` created."""

    id: str
    name: str
    description: NotRequired[str]
    domain: NotRequired[str]  # The full <subdomain>.squareweb.app host of a website.
    cluster: NotRequired[str]
    ram: int  # Memory in MB.
    cpu: float  # The allocated CPU.
    language: AppLanguage


class App(TypedDict):
    """An application's details."""

    id: str
    name: str
    desc: NotRequired[str]  # Left out when unset.
    owner: str  # The owner's user id.
    cluster: str
    ram: int  # Memory in MB.
    language: str  # Such as 'python' or 'javascript'.
    # The default <subdomain>.squareweb.app host, left out when there is none.
    domain: NotRequired[str | None]
    custom: NotRequired[str | None]  # The custom domain, left out when unset.
    created_at: str


class StatusListItem(TypedDict):
    """Whether one application or database is running, and its usage."""

    id: str
    running: bool
    cpu: NotRequired[str]  # Such as '0.50%', present only while running.
    ram: NotRequired[str]  # Such as '120.40MB', present only while running.


class StatsNetwork(TypedDict):
    """The network counters of :class:`RuntimeStats`."""

    total: str | list[int]  # A formatted string, or [in, out] numbers with raw=True.
    now: str | list[int]  # Like total.


class RuntimeStats(TypedDict):
    """The current usage of an application or database."""

    cpu: str | float  # Such as '0.5%', or a percentage with raw=True.
    ram: str | float  # Such as '120.4MB', or MB with raw=True.
    status: str  # Such as 'running' or 'exited'.
    running: bool
    storage: str | int  # A formatted size, or bytes with raw=True.
    network: StatsNetwork
    uptime: int | None  # Unix ms of the last start, or None when not running.
    restoring: NotRequired[bool]  # True while a snapshot restore is queued or running.


class MetricPoint(TypedDict):
    """One point of a usage history from ``metrics``."""

    date: str
    cpu: float  # Percent of the plan's CPU.
    ram: float  # Memory in MB.
    net: list[int]  # [bytes received, bytes sent] since the last start.
    # [bytes read, bytes written] since the last start, or None without a reading.
    disk: NotRequired[list[int] | None]
    storage: NotRequired[int | None]  # Bytes on disk, or None without a reading.
    cpu_max: NotRequired[float]  # The hour's peak CPU, only with range='7d'.
    ram_max: NotRequired[float]  # The hour's peak memory, only with range='7d'.


class AppDomain(TypedDict):
    """One domain of one of your applications."""

    app_id: str
    hostname: str
    # 'subdomain' is the default <name>.squareweb.app host.
    type: Literal['subdomain', 'custom']


class LoadBalancerApp(TypedDict):
    """An application that serves a custom domain."""

    id: str
    name: str
    cluster: NotRequired[str]


class LoadBalancer(TypedDict):
    """A custom domain and the applications that serve it."""

    hostname: str
    apps: list[LoadBalancerApp]


class LoadBalancers(TypedDict):
    """Your custom domains with the applications that serve each one."""

    limit: int  # How many applications your plan lets share one domain.
    balancers: list[LoadBalancer]


class DeployFiles(TypedDict):
    """The files a deploy added, removed and modified."""

    added: list[str]
    removed: list[str]
    modified: list[str]


class DeployEvent(TypedDict):
    """One step of a Git deploy."""

    id: str  # The commit SHA.
    state: Literal['pending', 'clone', 'commit', 'restarting', 'success', 'error']
    date: str
    source: Literal['git']
    branch: NotRequired[str]  # Present on 'clone' events.
    code: NotRequired[str]  # Why the deploy failed, on 'error' events.
    message: NotRequired[str]  # Details of the failure, on some 'error' events.
    files: NotRequired[DeployFiles]  # Present on 'commit' events.


class DeployRepository(TypedDict):
    """The GitHub repository linked to an application."""

    id: int | None
    name: str | None
    branch: str | None


class LinkedRepository(TypedDict):
    """The repository that ``apps.deploys.link_github_app`` linked."""

    id: int  # The GitHub repository id.
    full_name: str  # Such as 'owner/name'.
    branch: str


class DeployCurrent(TypedDict):
    """The GitHub App link and deploy webhook of an application."""

    # The linked repository, present when one is linked.
    app: NotRequired[DeployRepository]
    # The webhook URL. It is masked unless your API key may configure the webhook,
    # which needs the apps:deploy scope.
    webhook: NotRequired[str]


class FileEntry(TypedDict):
    """One file or directory of an application."""

    name: str  # The name, without the path.
    type: Literal['file', 'directory']
    size: NotRequired[int]  # Bytes, left out on some directories.
    # Unix ms, maybe with a fraction, or None when unreadable.
    lastModified: NotRequired[float | None]


# Snapshots ------------------------------------------------------------------


class Snapshot(TypedDict):
    """A stored snapshot of an application or a database."""

    name: str  # Pass it to restore.
    size: int  # Bytes.
    modified: str  # When it was stored.
    key: str  # The signed query string of the download URL.
    version_id: str  # Pass it to restore.
    url: str  # A signed download link, valid for 1 hour.
    # The engine or language it holds, or None on older snapshots.
    runtime: NotRequired[str | None]
    # 'automatic' for the daily snapshot, or None on older snapshots.
    origin: NotRequired[Literal['automatic', 'manual'] | None]


class SnapshotCreated(TypedDict):
    """The result of a snapshot ``create``."""

    pending: bool  # True while it is still being generated. Poll list for it.
    url: NotRequired[str]  # Only when not pending. '' without the snapshots:read scope.
    key: NotRequired[str]  # Like url.


class SnapshotRestored(TypedDict):
    """The result of a snapshot ``restore``."""

    pending: bool  # True while the restore still runs. Follow it with restore_state.


class SnapshotRestoreState(TypedDict):
    """The progress or outcome of the last snapshot restore."""

    # 'queued' or 'running' while it runs, then 'success' or 'error' for 1 hour after it
    # ends, or 'none'.
    state: Literal['none', 'queued', 'running', 'success', 'error']
    step: NotRequired[str]  # The current step, 'done' once it ends.
    code: NotRequired[str]  # Why it failed, when state is 'error'.
    started_at: NotRequired[int]  # Unix ms.
    finished_at: NotRequired[int]  # Unix ms, once it ends.


# Network --------------------------------------------------------------------


class AnalyticsFilters(TypedDict, total=False):
    """The optional filters of ``apps.network.analytics``."""

    country: str  # A two-letter code, such as 'BR'.
    ip: str
    path: str  # A path prefix, such as '/api'.
    status: str  # An HTTP status, such as '404'.
    os: str
    browser: str
    protocol: str
    referer: str  # 'Direct' matches requests without a referer.
    provider: str  # 'NAME (ASN)', such as 'GOOGLE (15169)'.
    content_type: str
    bot: str


class AnalyticsBucket(TypedDict):
    """One row of an analytics breakdown."""

    type: NotRequired[str]  # The value of the dimension. A provider is 'NAME (ASN)'.
    visits: int  # Unique visitors.
    requests: int
    bytes: int  # Response bytes served.
    bytes_in: NotRequired[int]  # Request bytes received, only in visits buckets.
    date: NotRequired[str]  # The start of the 15-minute window.


class NetworkAnalytics(TypedDict, total=False):
    """The traffic of an application's domains, broken down by dimension."""

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
    """The HTTP errors served on an application's domains."""

    summary: dict[str, Any]
    by_status: list[dict[str, Any]]  # A list of {status, requests}.
    timeseries: list[dict[str, Any]]
    top_paths: list[dict[str, Any]]
    by_method: list[dict[str, Any]]


class NetworkLog(TypedDict):
    """One request served on an application's domains."""

    timestamp: str
    client: dict[str, Any]
    request: dict[str, Any]
    response: dict[str, Any]


class NetworkPerformance(TypedDict, total=False):
    """The response times of an application's domains."""

    summary: dict[str, Any]
    timeseries: list[dict[str, Any]]
    countries: list[dict[str, Any]]
    colos: list[dict[str, Any]]  # By edge location.
    slowest_paths: list[dict[str, Any]]


class DNSRecord(TypedDict):
    """A DNS record to create for a custom domain."""

    type: Literal['txt', 'cname']
    name: str  # The record name to set at your DNS provider.
    value: str
    status: str  # Such as 'pending' or 'active'.
    # Up to 3 reasons why the record is not validated yet.
    errors: NotRequired[list[str]]
    # True on the one _acme-challenge CNAME that you can create instead of every TLS TXT
    # record.
    fallback: NotRequired[bool]


# Realtime -------------------------------------------------------------------


class LogEvent(TypedDict):
    """A log line from the live feed."""

    event: Literal['logs']
    data: str
    id: str | None
    stream: Literal['stdout', 'stderr']
    line: str  # The text without its stream marker.


class IOCounter(TypedDict, total=False):
    """A pair of input and output counters from the live feed."""

    i: float  # Received or read.
    o: float  # Sent or written.


class NetIO(IOCounter, total=False):
    """The network counters from the live feed."""

    new: IOCounter  # Bytes per second right now.


class RealtimeStatus(TypedDict, total=False):
    """The live state of an application, from a status event."""

    cpu: float
    cpuLimit: float  # CPU cores allocated.
    ram: list[float]  # [used MB, limit MB].
    status: str
    netIO: NetIO  # Network traffic.
    bIO: IOCounter  # Disk reads and writes.
    uptime: int  # Unix ms when the application started.


class StatusEvent(TypedDict):
    """A status update from the live feed."""

    event: Literal['status']
    data: str  # The raw frame.
    id: str | None
    status: RealtimeStatus  # The full state, with partial updates merged in.


class SystemEvent(TypedDict):
    """A system message, an error or an untyped message from the live feed."""

    # 'message' for a frame without an event type. Event types the API adds later arrive
    # in this shape too.
    event: Literal['system', 'error', 'message']
    data: str  # A code such as 'REALTIME_DISCONNECTED' or 'CONTAINER_NOT_FOUND'.
    id: str | None


RealtimeEvent = LogEvent | StatusEvent | SystemEvent
"""One event from the live feed. Check ``event`` to tell the shapes apart."""


# Databases ------------------------------------------------------------------


class DatabaseCreated(TypedDict):
    """The database that ``databases.create`` created, with its credentials."""

    id: str
    name: str
    memory: int  # Memory in MB.
    cpu: float  # The allocated CPU.
    type: DatabaseType
    password: str  # Shown only once.
    # Base64 PEM for TLS, or None when it could not be made.
    certificate: NotRequired[str | None]
    connection_url: str  # A connection string with the password included.
    cluster: str


class Database(TypedDict):
    """A database's details."""

    id: str
    name: str
    owner: str  # The owner's user id.
    cluster: str
    ram: int  # Memory in MB.
    type: DatabaseType
    port: int  # The TCP port.
    created_at: str


# Workspaces -----------------------------------------------------------------


class WorkspaceMember(TypedDict):
    """A member of a workspace."""

    id: str  # The member's user id.
    name: str | None  # None when it cannot be resolved, such as for a deleted account.
    group: Literal['owner', 'admin', 'maintain', 'manager', 'view']
    joinedAt: str


class WorkspaceApp(TypedDict):
    """An application shared with a workspace."""

    id: str  # The plain application id. Use f'{id}-{workspace_id}' to act on it.
    name: str
    desc: str | None  # None when unset.
    ram: int  # Memory in MB.
    lang: str
    domain: NotRequired[str | None]  # Left out when unset.
    custom: NotRequired[str | None]  # Left out when unset.


class Workspace(TypedDict):
    """A workspace with its members and shared applications."""

    id: str  # 32 or 40 hex characters.
    name: str
    owner: str  # The owner's user id.
    members: list[WorkspaceMember]
    applications: list[WorkspaceApp]
    createdAt: str


class WorkspaceCreated(TypedDict):
    """The workspace that ``workspaces.create`` created."""

    id: str
    name: str
