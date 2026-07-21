import contextvars
from ecip_core.config.loader import settings
from ecip_core.graph.provider import GraphProvider

# Thread-safe ContextVar caches for provider instances
_sqlite_provider_var = contextvars.ContextVar("sqlite_provider", default=None)
_neo4j_provider_var = contextvars.ContextVar("neo4j_provider", default=None)


def get_graph_provider() -> GraphProvider:
    """
    Factory to retrieve or initialize the active GraphProvider singleton per execution context.
    """
    provider_name = settings.graph.provider.lower()
    
    if provider_name == "neo4j":
        provider = _neo4j_provider_var.get()
        if provider is None:
            from ecip_core.providers.graph.neo4j_provider import Neo4jGraphProvider
            provider = Neo4jGraphProvider(
                uri=settings.graph.neo4j_uri,
                username=settings.graph.neo4j_username,
                password=settings.graph.neo4j_password
            )
            provider.connect()
            _neo4j_provider_var.set(provider)
        return provider
    else:
        provider = _sqlite_provider_var.get()
        if provider is None:
            from ecip_core.providers.graph.sqlite_provider import SqliteGraphProvider
            provider = SqliteGraphProvider()
            provider.connect()
            _sqlite_provider_var.set(provider)
        return provider
