import pyarrow as pa
from pyiceberg.catalog import load_catalog
from requests.exceptions import ConnectionError as RequestsConnectionError


class Iceberg:
    def __init__(self, iceberg_catalog_uri: str = "http://iceberg-rest:8181"):
        try:
            self._catalog = load_catalog(
                "rest",
                **{
                    "type": "rest",
                    "uri": iceberg_catalog_uri,
                },
            )
        except RequestsConnectionError:
            if iceberg_catalog_uri == "http://iceberg-rest:8181":
                self._catalog = load_catalog(
                    "rest",
                    **{
                        "type": "rest",
                        "uri": "http://localhost:8181",
                    },
                )
            else:
                raise

    @property
    def catalog(self):
        return self._catalog
