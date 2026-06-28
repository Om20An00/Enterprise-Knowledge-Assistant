
from pathlib import Path
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from .preprocessing.preprocessor import Preprocessor
from .chunks.chunker import Chunker
from .embeddings.embedder import Embedder
from app.modules.documents.storage_utils import SupabaseStorage
from app.modules.documents.repository import DocumentRepository
from app.modules.chat.pricing import calculate_indexing_cost
import tempfile
import os


class IngestionPipeline:
  
    
    def __init__(self, db_session: Session, storage: SupabaseStorage):
        self.db = db_session
        self.storage = storage
        
       
        self.preprocessor = Preprocessor()
        self.chunker = Chunker()
        self.embedder = Embedder(db_session)
        self.repository = DocumentRepository(db_session)
    
    
    def process_documents(self, document_ids: List[int]) -> List[Dict[str, Any]]:
        results = []
        
        for document_id in document_ids:
            temp_file_path = None
            try:
                
                document = self.repository.get_document_by_id(document_id)
                if not document:
                    raise ValueError(f"Document with id {document_id} not found")
                
               
                file_content = self.storage.download_file(document.file_path)
              
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=Path(document.filename).suffix)
                temp_file.write(file_content)
                temp_file.close()
                temp_file_path = Path(temp_file.name)
              
                self.repository.update_document_status(document_id, "processing")
              
                temp_filename = temp_file_path.name
                filename_mapping = {temp_filename: document.filename}
                process_results = self.preprocessor.process_files([temp_file_path], filename_mapping)
                docs = process_results.get(temp_filename, [])
                
                if not docs:
                    self.repository.update_document_status(document_id, "failed")
                    raise ValueError(f"No content could be extracted from {document.filename}")
              
                final_chunks = self.chunker.chunk_documents(docs)
                
                if not final_chunks:
                    self.repository.update_document_status(document_id, "failed")
                    raise ValueError(f"No chunks could be created from {document.filename}")
               
                indexing_cost = calculate_indexing_cost(final_chunks)
               
                stored_count = self.embedder.generate_and_store_embeddings(final_chunks, document_id)
             
                self.repository.update_document_processing_result(
                    document_id, 
                    chunks_count=len(final_chunks), 
                    status="processed",
                    indexing_cost=indexing_cost
                )
                
                results.append({
                    "document_id": document_id,
                    "filename": document.filename,
                    "status": "processed",
                    "chunks_count": len(final_chunks),
                    "embeddings_stored": stored_count,
                    "indexing_cost": indexing_cost
                })
                
            except Exception as e:
              
                self.repository.update_document_status(document_id, "failed")
                results.append({
                    "document_id": document_id,
                    "status": "failed",
                    "error": str(e)
                })
            finally:
             
                if temp_file_path and temp_file_path.exists():
                    try:
                        os.unlink(temp_file_path)
                    except Exception as e:
                        print(f"Warning: Could not delete temp file {temp_file_path}: {e}")
        
        return results
    
    def validate_file_for_processing(self, file_path: str) -> bool:

        if not self.storage.file_exists(file_path):
            return False
        
        return self.preprocessor.is_supported_file(Path(file_path))
