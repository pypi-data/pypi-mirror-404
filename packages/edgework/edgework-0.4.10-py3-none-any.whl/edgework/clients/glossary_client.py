from edgework.http_client import HttpClient
from edgework.models.glossary import Glossary, Term


class GlossaryClient:
    def __init__(self, client: HttpClient):
        self._client = client

    def get_glossary(self) -> Glossary:
        response = self._client.get("stats/rest/en/glossary", web=False)
        terms = [Term(**term) for term in response.json()["data"]]
        return Glossary(terms=terms)
