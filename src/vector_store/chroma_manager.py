"""
Gerenciador do ChromaDB para busca semântica.
"""
from pathlib import Path

from ..config import CHROMA_STORE_PATH, settings


class ChromaManager:
    """Gerencia coleção ChromaDB embedded para busca vetorial."""

    COLLECTION_NAME = "ddl_objects"

    def __init__(self, persist_dir: Path | None = None):
        self.persist_dir = str(persist_dir or CHROMA_STORE_PATH)
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self._client = chromadb.Client(ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.persist_dir,
                anonymized_telemetry=False,
            ))
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def recreate_collection(self):
        """Apaga e recria a coleção."""
        client = self._get_client()
        try:
            client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass
        self._collection = None
        return self._get_collection()

    def add_documents(self, documents: list[dict]):
        """
        Adiciona documentos com embeddings ao ChromaDB.
        Cada doc deve ter: id, text, embedding, metadata
        """
        collection = self._get_collection()

        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            collection.add(
                ids=[d["id"] for d in batch],
                embeddings=[d["embedding"] for d in batch],
                documents=[d["text"] for d in batch],
                metadatas=[d["metadata"] for d in batch],
            )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """
        Busca semântica por embedding.
        Retorna lista de resultados com: id, text, metadata, distance.
        """
        collection = self._get_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                items.append({
                    "id": doc_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return items

    def search_text(self, query_text: str, top_k: int = 5) -> list[dict]:
        """
        Busca semântica por texto (gera embedding internamente via ChromaDB).
        """
        collection = self._get_collection()
        results = collection.query(
            query_texts=[query_text],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                items.append({
                    "id": doc_id,
                    "text": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return items

    def count(self) -> int:
        return self._get_collection().count()

    def persist(self):
        client = self._get_client()
        if hasattr(client, 'persist'):
            client.persist()
