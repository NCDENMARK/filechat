import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from config import OPENAI_CLIENT, CHROMA_PERSIST_DIR, COLLECTION_NAME


class VectorStore:
    def __init__(self):
        # Create/connect to local ChromaDB database
        self.client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=Settings(anonymized_telemetry=False)
        )
        # Get or create a collection (like a table) for our documents
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME
        )
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Convert text into numerical vectors that capture meaning"""
        try:
            response = OPENAI_CLIENT.embeddings.create(
                model="text-embedding-3-small",  # stable embedding model
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error creating embeddings: {e}")
            return []
    
    def add_documents(self, chunks: List[str], metadata: Dict, file_id: str):
        """Store document chunks in the vector database"""
        if not chunks:
            return
        
        embeddings = self.create_embeddings(chunks)
        if not embeddings:
            print("Failed to create embeddings")
            return
        
        ids = [f"{file_id}_{i}" for i in range(len(chunks))]
        
        metadatas = [
            {
                "file_name": metadata["file_name"],
                "file_path": metadata["file_path"],
                "file_type": metadata.get("file_type", "PDF"),
                "folder_path": metadata.get("folder_path", ""),
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]
        
        self.collection.add(
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"Successfully added {len(chunks)} chunks from {metadata['file_name']}")
    
    def search(self, query: str, n_results: int = 5, folder_path: Optional[str] = None) -> Dict:
        """Find chunks most similar to the user's question
        
        Args:
            query: The search query
            n_results: Number of results to return
            folder_path: Optional folder path to filter results
        """
        query_embedding = self.create_embeddings([query])
        if not query_embedding:
            return {"documents": [], "metadatas": []}
        
        # Build where clause for folder filtering
        where_clause = None
        if folder_path:
            where_clause = {"folder_path": folder_path}
        
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results,
            where=where_clause
        )
        return results
    
    def get_indexed_folders(self) -> List[str]:
        """Get list of all unique folder paths that have been indexed"""
        try:
            # Get all documents (limit to avoid memory issues with large collections)
            all_docs = self.collection.get(limit=10000)
            
            # Extract unique folder paths
            folders = set()
            if all_docs and 'metadatas' in all_docs:
                for metadata in all_docs['metadatas']:
                    folder_path = metadata.get('folder_path', '')
                    if folder_path:
                        folders.add(folder_path)
            
            return sorted(list(folders))
        except Exception as e:
            print(f"Error getting indexed folders: {e}")
            return []
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            # Delete the old collection
            try:
                self.client.delete_collection(name=COLLECTION_NAME)
                print(f"Deleted collection '{COLLECTION_NAME}'")
            except Exception as e:
                print(f"Note: Could not delete collection (may not exist): {e}")
            
            # Force recreate the collection with the correct name
            self.collection = self.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"description": "FileChat documents collection"}
            )
            print(f"Collection '{COLLECTION_NAME}' recreated successfully")
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            # Try to get existing collection as fallback
            try:
                self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
                print(f"Fallback: Using existing collection '{COLLECTION_NAME}'")
                return True
            except Exception as e2:
                print(f"Fallback failed: {e2}")
                return False