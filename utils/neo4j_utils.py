def insert_defect(tx, defect_data: dict):
    """
    Insert or update a defect node with attributes, tags, comments, and linked defects.

    defect_data example keys:
      - defect_id (str)
      - title (str)
      - description (str)
      - status (str)
      - created_date (str or datetime)
      - updated_date (str or datetime)
      - created_by (str)
      - updated_by (str)
      - tags (list of str)
      - comments (list of dicts with keys: commenter, comment_text, comment_date)
      - linked_defects (list of defect_ids)
    """
    tx.run(
        """
        MERGE (d:Defect {defect_id: $defect_id})
        SET d.title = $title,
            d.description = $description,
            d.status = $status,
            d.created_date = $created_date,
            d.updated_date = $updated_date,
            d.created_by = $created_by,
            d.updated_by = $updated_by
        """,
        **defect_data
    )

    for tag in defect_data.get("tags", []):
        tx.run(
            """
            MERGE (t:Tag {name: $tag})
            WITH t
            MATCH (d:Defect {defect_id: $defect_id})
            MERGE (d)-[:HAS_TAG]->(t)
            """,
            tag=tag,
            defect_id=defect_data["defect_id"]
        )

    for comment in defect_data.get("comments", []):
        tx.run(
            """
            MERGE (c:Comment {
                commenter: $author,
                comment_text: $text,
                comment_date: $commented_on
            })
            WITH c
            MATCH (d:Defect {defect_id: $defect_id})
            MERGE (d)-[:HAS_COMMENT]->(c)
            """,
            **comment,
            defect_id=defect_data["defect_id"]
        )

    for linked_id in defect_data.get("linked_defects", []):
        tx.run(
            """
            MATCH (d1:Defect {defect_id: $defect_id})
            MATCH (d2:Defect {defect_id: $linked_id})
            MERGE (d1)-[:LINKED_TO]->(d2)
            """,
            defect_id=defect_data["defect_id"],
            linked_id=linked_id
        )

def fetch_all_defects(tx):
    """
    Fetch all defect nodes with their tags, comments, and linked defects.
    Returns a list of dicts with defect details.
    """
    query = """
    MATCH (d:Defect)
    OPTIONAL MATCH (d)-[:HAS_TAG]->(t:Tag)
    OPTIONAL MATCH (d)-[:HAS_COMMENT]->(c:Comment)
    OPTIONAL MATCH (d)-[:LINKED_TO]->(ld:Defect)
    RETURN
      d.defect_id AS defect_id,
      d.title AS title,
      d.description AS description,
      d.status AS status,
      d.created_date AS created_date,
      d.updated_date AS updated_date,
      d.created_by AS created_by,
      d.updated_by AS updated_by,
      collect(DISTINCT t.name) AS tags,
      collect(DISTINCT {commenter: c.commenter, comment_text: c.comment_text, comment_date: c.comment_date}) AS comments,
      collect(DISTINCT ld.defect_id) AS linked_defects
    """
    result = tx.run(query)
    return [record.data() for record in result]

def delete_all_defects(tx):
    """Delete all Defect nodes and their relationships."""
    tx.run("MATCH (d:Defect) DETACH DELETE d")

def fetch_defect_by_id(tx, defect_id):
    query = """
    MATCH (d:Defect {id: $defect_id})
    RETURN d.id AS defect_id, d.title AS title, d.description AS description,
           d.status AS status, d.tags AS tags, d.comments AS comments
    """
    result = tx.run(query, defect_id=defect_id)
    record = result.single()
    if record:
        return {
            "defect_id": record["defect_id"],
            "title": record["title"],
            "description": record["description"],
            "status": record["status"],
            "tags": record.get("tags", []),
            "comments": record.get("comments", []),
        }
    return None

