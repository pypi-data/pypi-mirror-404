import logging
from agentfoundry.vectorstores.providers.chroma_client import ChromaDBClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def describe_collections(persist_directory: str):
    """
    Retrieve and print descriptive information about all collections in ChromaDB.

    Args:
        persist_directory (str): Directory where ChromaDB persists data.
    """
    # Initialize the client
    client = ChromaDBClient()

    # List all collection names
    collection_objs = client.client.list_collections()
    logger.info(f"Found {len(collection_objs)} collections")

    # Gather details for each collection
    for col in collection_objs:
        name = getattr(col, "name", str(col))
        # Get the collection object
        collection = client.client.get_collection(name)

        # Get basic info
        item_count = collection.count()
        metadata = collection.metadata or {}

        # Construct a description
        description = metadata.get("description", "No description provided")
        source = metadata.get("source", "Unknown source")
        created_by = metadata.get("created_by", "Unknown creator")

        # Log and print the details
        logger.info(f"Collection: {name}")
        logger.info(f"  Item Count: {item_count}")
        logger.info(f"  Description: {description}")
        logger.info(f"  Source: {source}")
        logger.info(f"  Created By: {created_by}")
        logger.info(f"  Full Metadata: {metadata}")
        print(f"\nCollection: {name}")
        print(f"  Item Count: {item_count}")
        print(f"  Description: {description}")
        print(f"  Source: {source}")
        print(f"  Created By: {created_by}")
        print(f"  Full Metadata: {metadata}")


# Test the function
if __name__ == "__main__":
    persist_dir = "./quantumdrive/chromadb"
    describe_collections(persist_dir)
