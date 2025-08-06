from config.neo4j_conn import get_neo4j_driver

def test_neo4j_connection():
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("RETURN 1 AS test")
        val = result.single()["test"]
        assert val == 1
        print("✅ Neo4j connection test passed!")
    driver.close()

if __name__ == "__main__":
    test_neo4j_connection()
