
from typing import List
from langchain.text_splitter import MarkdownHeaderTextSplitter, TokenTextSplitter
from langchain.schema import Document
import re


class Chunker:
   
    
    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 10):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
  
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2")
            ]
        )
        
        self.token_splitter = TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
      
        markdown_chunks = []
        
        for doc in documents:
            parts = self.markdown_splitter.split_text(doc.page_content)
            for part in parts:
                part.metadata.update(doc.metadata)
                markdown_chunks.append(part)
        
       
        final_chunks = []
        
        for chunk in markdown_chunks:
            token_chunks = self.token_splitter.split_text(chunk.page_content)
            
            for i, token_text in enumerate(token_chunks):
               
                page_markers = re.findall(r'<!--PAGE_(\d+)-->', token_text)
             
                clean_text = re.sub(r'<!--PAGE_\d+-->', '', token_text).strip()
             
                metadata = {**chunk.metadata, "split_id": i}
                for key in ['h1', 'h2', 'h3']:
                    if key in metadata and metadata[key]:
                        metadata[key] = re.sub(r'\s*<!--PAGE_\d+-->', '', metadata[key]).strip()
             
                if page_markers:
                    min_page = min(int(p) for p in page_markers)
                    metadata["page"] = min_page
                
                final_chunks.append(
                    Document(
                        page_content=clean_text,
                        metadata=metadata
                    )
                )
        
        return final_chunks
