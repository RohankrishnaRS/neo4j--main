from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

if not uri or not user or not password:
    print("NEO4J configuration missing. Set NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env or environment.")
else:
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run("RETURN 1 AS num")
            print(result.single()["num"])
    except Exception as e:
        print("ERROR:", e)
