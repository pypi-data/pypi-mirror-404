import duckdb

class DuckDB():
    def __init__(self, endpoint: str = "http://iceberg-rest:8181"):
        self._connection = self.connect(endpoint)

    @property
    def connection(self):
        return self._connection

    def connect(self, endpoint="http://iceberg-rest:8181"):
        conn = duckdb.connect()
        conn.execute("INSTALL iceberg; LOAD iceberg;")
        try:
            conn.execute(f"""
                ATTACH '' AS iceberg (
                    TYPE iceberg,
                    ENDPOINT '{endpoint}',
                    AUTHORIZATION_TYPE 'none'
                )
            """)
        except duckdb.IOException:
            if endpoint == "http://iceberg-rest:8181":
                conn.execute("""
                    ATTACH '' AS iceberg (
                        TYPE iceberg,
                        ENDPOINT 'http://localhost:8181',
                        AUTHORIZATION_TYPE 'none'
                    )
                """)
            else:
                raise
        return conn