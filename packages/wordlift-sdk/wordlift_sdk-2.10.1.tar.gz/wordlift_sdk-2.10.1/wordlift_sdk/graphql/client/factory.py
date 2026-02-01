from gql import Client
from gql.transport.aiohttp import AIOHTTPTransport

from .client import GraphQlClient
from .gql_client_provider import GqlClientProvider


class GraphQlClientFactory:
    _api_url: str
    _key: str

    def __init__(self, key: str, api_url: str = "https://api.wordlift.io/graphql"):
        self._api_url = api_url
        self._key = key

    def create(self) -> GraphQlClient:
        return GraphQlClient(self.create_provider())

    def create_transport(self) -> AIOHTTPTransport:
        # Select your transport with a defined url endpoint
        return AIOHTTPTransport(
            url=self._api_url,
            ssl=True,
            headers={"Authorization": f"Key {self._key}", "X-include-Private": "true"},
        )

    def create_gql_client(self) -> Client:
        # Create a GraphQL client using the defined transport
        return Client(
            transport=self.create_transport(),
            fetch_schema_from_transport=False,
            execute_timeout=120,
        )

    def create_provider(self) -> GqlClientProvider:
        return GqlClientProvider(key=self._key, api_url=self._api_url)
