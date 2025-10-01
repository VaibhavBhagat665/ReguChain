"""
Pathway Embeddings Pipeline
Processes documents through OpenRouter embeddings and FAISS indexing
"""
import pathway as pw
import asyncio
import logging
from typing import Dict, Any, List
from ..openrouter_embeddings import embeddings_client
from ..vector_store import vector_store
from ..database import database

logger = logging.getLogger(__name__)

class EmbeddingsPathwayPipeline:
    """Pathway-powered embeddings and indexing pipeline"""
    
    def __init__(self):
        self.processed_docs = set()
        
    def create_embeddings_pipeline(self, source_table: pw.Table):
        """Create Pathway pipeline for embeddings and indexing"""
        
        @pw.udf
        def process_embeddings(docs: pw.Table) -> pw.Table:
            """Process documents through embeddings and indexing"""
            processed_docs = []
            
            # Convert Pathway table to list of dicts
            doc_list = docs.to_pandas().to_dict('records') if not docs.is_empty() else []
            
            if not doc_list:
                return pw.Table.empty()
            
            logger.info(f"🔄 Processing {len(doc_list)} documents for embeddings...")
            
            # Process in batches
            batch_size = 10
            for i in range(0, len(doc_list), batch_size):
                batch = doc_list[i:i + batch_size]
                
                try:
                    # Extract texts for embedding
                    texts = [doc.get('text', '') for doc in batch]
                    
                    # Generate embeddings using OpenRouter
                    embeddings = asyncio.run(embeddings_client.embed_texts(texts))
                    
                    if not embeddings:
                        logger.error(f"Failed to generate embeddings for batch {i//batch_size + 1}")
                        continue
                    
                    # Process each document with its embedding
                    for doc, embedding in zip(batch, embeddings):
                        try:
                            doc_id = doc.get('id', '')
                            
                            # Skip if already processed
                            if doc_id in self.processed_docs:
                                continue
                            
                            # Store in vector store
                            vector_store.add_document(
                                doc_id=doc_id,
                                content=doc.get('text', ''),
                                embedding=embedding,
                                metadata=doc.get('metadata', {})
                            )
                            
                            # Store in database
                            asyncio.run(database.store_document(doc))
                            
                            # Mark as processed
                            self.processed_docs.add(doc_id)
                            
                            # Add processing metadata
                            processed_doc = {
                                **doc,
                                'embedding_stored': True,
                                'embedding_dimension': len(embedding),
                                'processed_timestamp': pw.this.processed_at
                            }
                            processed_docs.append(processed_doc)
                            
                        except Exception as e:
                            logger.error(f"Error processing document {doc.get('id', 'unknown')}: {e}")
                            continue
                    
                    logger.info(f"✅ Processed batch {i//batch_size + 1}/{(len(doc_list) + batch_size - 1)//batch_size}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing batch {i//batch_size + 1}: {e}")
                    continue
            
            logger.info(f"🎯 Successfully processed {len(processed_docs)} documents with embeddings")
            return pw.Table.from_pandas(pw.pandas.DataFrame(processed_docs)) if processed_docs else pw.Table.empty()
        
        # Apply embeddings processing to source table
        embedded_docs = source_table.select(
            processed_data=process_embeddings(pw.this)
        ).flatten(pw.this.processed_data)
        
        return embedded_docs
    
    def create_indexing_pipeline(self, embedded_table: pw.Table):
        """Create pipeline for FAISS index updates"""
        
        @pw.udf
        def update_index_stats(docs: pw.Table) -> pw.Table:
            """Update index statistics and metadata"""
            doc_list = docs.to_pandas().to_dict('records') if not docs.is_empty() else []
            
            if not doc_list:
                return pw.Table.empty()
            
            # Get current index stats
            stats = vector_store.get_stats()
            
            # Update stats with new documents
            updated_stats = []
            for doc in doc_list:
                stat_entry = {
                    'doc_id': doc.get('id', ''),
                    'source': doc.get('source', ''),
                    'type': doc.get('type', ''),
                    'risk_level': doc.get('metadata', {}).get('risk_level', 'low'),
                    'indexed_at': doc.get('processed_timestamp', ''),
                    'total_docs_in_index': stats.get('documents', 0),
                    'index_dimension': stats.get('dimension', 0)
                }
                updated_stats.append(stat_entry)
            
            logger.info(f"📊 Updated index stats for {len(updated_stats)} documents")
            return pw.Table.from_pandas(pw.pandas.DataFrame(updated_stats))
        
        # Apply index stats update
        index_stats = embedded_table.select(
            stats_data=update_index_stats(pw.this)
        ).flatten(pw.this.stats_data)
        
        return index_stats

# Global instance
embeddings_pathway_pipeline = EmbeddingsPathwayPipeline()
