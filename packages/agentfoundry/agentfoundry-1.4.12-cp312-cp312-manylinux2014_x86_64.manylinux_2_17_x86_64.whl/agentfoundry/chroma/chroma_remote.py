__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "10/25/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import chromadb
chroma_client = chromadb.HttpClient(host='chroma.quantify.alphasixdemo.com', ssl=True, port=443)

try:
    collection = chroma_client.create_collection(name="my_test_collection")
    print("Collection created successfully")
except Exception as e:
    print(f"Error creating collection: {e}")