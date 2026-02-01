__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "2/25/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

# agentfoundry/chromadb/data_loader.py

import json  # For JSON serialization
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List

from pypdf import PdfReader

from agentfoundry.vectorstores.providers.chroma_client import ChromaDBClient
from agentfoundry.utils.config import Config


class ChromaDBDataLoader:
    def __init__(self, data_directory: str, persist_directory: str, collection_name: str, chunk_size: int = 512):
        self.logger = logging.getLogger(__name__)
        self.data_directory = data_directory
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.chunk_size = chunk_size

        self.client = ChromaDBClient()
        self.logger.info(f"Initialized ChromaDBDataLoader with data_directory: {data_directory}, collection: {collection_name}")

    def load_pdfs(self) -> int:
        if not os.path.exists(self.data_directory):
            self.logger.error(f"Data directory does not exist: {self.data_directory}")
            raise FileNotFoundError(f"Data directory does not exist: {self.data_directory}")

        total_chunks = 0
        pdf_files = [f for f in os.listdir(self.data_directory) if f.lower().endswith('.pdf')]

        if not pdf_files:
            self.logger.warning(f"No PDF files found in {self.data_directory}")
            return 0

        self.logger.info(f"Found {len(pdf_files)} PDF files to process")

        collection_metadata = {
            "description": f"Documents from {self.data_directory.split('/')[-1]} directory",
            "category": "Capabilities",
            "source": self.data_directory,
            "keywords": json.dumps(["capabilities"]),
            "created_at": datetime.now(timezone.utc).isoformat() + "Z"
        }

        collection = self.client.client.get_or_create_collection(
            name=self.collection_name,
            metadata=collection_metadata,
            embedding_function=self.client.embedding_function
        )

        all_keywords = set()
        for pdf_file in pdf_files:
            pdf_path = os.path.join(self.data_directory, pdf_file)
            chunks = self._parse_and_chunk_pdf(pdf_path)
            if chunks:
                self._store_chunks(chunks, pdf_file)
                total_chunks += len(chunks)
                for chunk in chunks:
                    # Parse keywords from the JSON string stored in metadata
                    chunk_keywords = json.loads(chunk["metadata"].get("keywords", "[]"))
                    all_keywords.update(chunk_keywords)

        collection_metadata["keywords"] = json.dumps(list(all_keywords))
        collection.modify(metadata=collection_metadata)
        self.logger.info(f"Processed {len(pdf_files)} PDFs, stored {total_chunks} chunks, keywords: {all_keywords}")

        return total_chunks

    def _parse_and_chunk_pdf(self, pdf_path: str) -> List[Dict]:
        try:
            self.logger.info(f"Parsing PDF: {pdf_path}")
            pdf_reader = PdfReader(pdf_path)
            num_pages = len(pdf_reader.pages)
            full_text = ""

            doc_info = pdf_reader.metadata or {}
            author = doc_info.get("/Author", "Unknown")
            title = doc_info.get("/Title", os.path.basename(pdf_path))
            creation_date = doc_info.get("/CreationDate", "Unknown")

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text:
                    full_text += text + "\n"

            if not full_text.strip():
                self.logger.warning(f"No text extracted from {pdf_path}")
                return []

            chunks = self._chunk_text(full_text, pdf_path, {
                "source": os.path.basename(pdf_path),
                "author": author,
                "title": title,
                "creation_date": creation_date,
                "document_type": "PDF",
                "category": "Capabilities"
            })
            self.logger.info(f"Extracted {len(chunks)} chunks from {pdf_path}")
            return chunks

        except Exception as e:
            self.logger.error(f"Failed to parse PDF {pdf_path}: {str(e)}")
            return []

    def _chunk_text(self, text: str, pdf_path: str, base_metadata: Dict) -> List[Dict]:
        chunks = []
        current_chunk = ""
        chunk_number = 1
        if pdf_path:
            self.logger.info(f"Parsing PDF: {pdf_path}")
        paragraphs = text.split("\n\n")
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue

            if len(current_chunk) + len(paragraph) <= self.chunk_size:
                current_chunk += paragraph + "\n\n"
            else:
                if current_chunk:
                    chunk_metadata = base_metadata.copy()
                    chunk_metadata.update({
                        "chunk_number": chunk_number,
                        "keywords": json.dumps(self._extract_keywords(current_chunk)),  # Serialize keywords to string
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    })
                    chunks.append({
                        "text": current_chunk.strip(),
                        "metadata": chunk_metadata
                    })
                    chunk_number += 1
                current_chunk = paragraph + "\n\n"

                while len(current_chunk) > self.chunk_size:
                    split_point = current_chunk.rfind(" ", 0, self.chunk_size)
                    if split_point == -1:
                        split_point = self.chunk_size
                    chunk_metadata = base_metadata.copy()
                    chunk_metadata.update({
                        "chunk_number": chunk_number,
                        "keywords": json.dumps(self._extract_keywords(current_chunk[:split_point])),
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    })
                    chunks.append({
                        "text": current_chunk[:split_point].strip(),
                        "metadata": chunk_metadata
                    })
                    chunk_number += 1
                    current_chunk = current_chunk[split_point:].strip() + "\n\n"

        if current_chunk.strip():
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_number": chunk_number,
                "keywords": json.dumps(self._extract_keywords(current_chunk)),
                "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
            })
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": chunk_metadata
            })

        return chunks

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        stop_words = {"the", "and", "to", "of", "in", "a", "is", "for", "with"}
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        keywords = sorted(word_freq, key=word_freq.get, reverse=True)[:5]
        return keywords if keywords else ["unknown"]

    def _store_chunks(self, chunks: List[Dict], pdf_file: str):
        if not chunks:
            self.logger.warning(f"No chunks to store from {pdf_file}")
            return

        # Persist chunks via the LangChain Chroma wrapper
        store = self.client.as_vectorstore(collection=self.collection_name)
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        try:
            store.add_texts(texts, metadatas=metadatas)
        except Exception:
            from langchain_core.documents import Document
            docs = [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]
            store.add_documents(docs)
        self.logger.info(f"Stored {len(chunks)} chunks from {pdf_file}")


# Test routine
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Set up command-line argument parsing
    # parser = argparse.ArgumentParser(description="Load PDFs into ChromaDB")
    # parser.add_argument("data_dir", help="Path to the directory containing PDF files")
    # args = parser.parse_args()

    # Use the command-line input for data_dir
    # data_dir = args.data_dir
    data_dir = Config().get("DATA_DIR", None)
    capabilities_dir = os.path.join(data_dir, "capabilities")

    persist_dir = Config().get("CHROMADB.PERSIST_DIR")
    collection_name = Config().get("CHROMA.COLLECTION_NAME")
    os.environ["HF_TOKEN"] = Config().get("HF_TOKEN")

    loader = ChromaDBDataLoader(
        data_directory=capabilities_dir,
                # persistence handled internally
        collection_name=collection_name,
        chunk_size=512
    )
    total_chunks = loader.load_pdfs()
    print(f"Total chunks stored: {total_chunks}")

    collection_names = loader.client.client.list_collections()
    print("\nAvailable collections:")
    for col in collection_names:
        name = getattr(col, "name", str(col))
        collection = loader.client.client.get_collection(name)
        print(f"\tName: {collection.name}")
        print(f"\tItem Count: {collection.count()}")
        print(f"\tMetadata: {collection.metadata}")
