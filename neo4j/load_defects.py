import json
from config.neo4j_conn import get_neo4j_driver
from utils.neo4j_utils import insert_defect, delete_all_defects

# --- Load defect data ---
defects_file = "data/insurance_defects_detailed.json"
with open(defects_file, "r", encoding="utf-8") as f:
    defects = json.load(f)

def load_all_defects():
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Delete all existing defects first
        session.write_transaction(delete_all_defects)
        print("🗑️ Deleted all existing defects from Neo4j.")

        #Load only first 2 defects for testing
        for defect in defects[:2]:
            formatted_defect = {
                "defect_id": defect.get("id"),
                "title": defect.get("summary"),
                "description": defect.get("description"),
                "status": defect.get("status"),
                "created_date": defect.get("created_on"),
                "updated_date": defect.get("updated_on"),
                "created_by": defect.get("created_by", "unknown"),
                "updated_by": defect.get("updated_by", "unknown"),
                "tags": defect.get("tags", []),
                "comments": defect.get("comments", []),
                "linked_defects": defect.get("related_defects", []),
            }
            session.write_transaction(insert_defect, formatted_defect)
        print(f"✅ Loaded 2 defects into Neo4j for testing")

if __name__ == "__main__":
    load_all_defects()
