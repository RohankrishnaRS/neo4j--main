from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()


class Neo4jClient:

    def __init__(self):

        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")

        if not uri or not user or not password:
            self.driver = None
            return

        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            connection_timeout=30,
            max_connection_lifetime=1000,
        )

    def create_node(self, label, props):

        if not self.driver:
            raise RuntimeError(
                "Neo4j not configured. Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD."
            )

        safe_label = (
            label.replace(" ", "_")
            .replace(".", "_")
            .replace("-", "_")
            .replace("/", "_")
            .replace("'", "_")
            .replace('"', "_")
            .replace(":", "_")
            .replace(";", "_")
        )

        cypher = f"""
        MERGE (n:{safe_label} {{name: $name}})
        SET n += $props
        RETURN n
        """

        with self.driver.session(database="neo4j") as session:
            session.run(
                cypher,
                name=props["name"],
                props=props
            )

    def create_relationship(
        self,
        from_label: str,
        to_label: str,
        rel_type: str,
        from_props: dict,
        to_props: dict
    ):

        if not self.driver:
            raise RuntimeError(
                "Neo4j not configured."
            )

        safe_from_label = (
            from_label.replace(" ", "_")
            .replace(".", "_")
            .replace("-", "_")
            .replace("/", "_")
            .replace("'", "_")
            .replace('"', "_")
            .replace(":", "_")
            .replace(";", "_")
        )

        safe_to_label = (
            to_label.replace(" ", "_")
            .replace(".", "_")
            .replace("-", "_")
            .replace("/", "_")
            .replace("'", "_")
            .replace('"', "_")
            .replace(":", "_")
            .replace(";", "_")
        )

        safe_rel_type = (
            rel_type.upper()
            .replace(" ", "_")
            .replace(".", "_")
            .replace("-", "_")
            .replace("/", "_")
            .replace("'", "_")
            .replace('"', "_")
            .replace(":", "_")
            .replace(";", "_")
        )

        cypher = f"""
        MERGE (a:{safe_from_label} {{name: $from_name}})
        MERGE (b:{safe_to_label} {{name: $to_name}})
        MERGE (a)-[r:{safe_rel_type}]->(b)
        RETURN r
        """

        with self.driver.session(database="neo4j") as session:
            session.run(
                cypher,
                from_name=from_props["name"],
                to_name=to_props["name"]
            )

    def query(self, cypher):

        if not self.driver:
            raise RuntimeError(
                "Neo4j not configured."
            )

        with self.driver.session(database="neo4j") as session:
            result = session.run(cypher)
            return [r.data() for r in result]

    def close(self):

        if self.driver:
            self.driver.close()