import asyncio
from langchain_community.vectorstores import Chroma
from langchain_openai import AzureOpenAIEmbeddings
from app.core.config import settings
from app.services.metadata_service import MetadataEnricher # Your new class

class VectorService:
    def __init__(self):
        print("Vector srvice got initiated")
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            openai_api_version=settings.OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
        )
        self.enricher = MetadataEnricher()
        print("Assigned self")

    async def create_vector_store(self, raw_documents):
        """
        Logic: Chunks -> Enrich (Parallel) -> Embed -> Store
        """
        # 1. Standard Chunking
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        chunks = text_splitter.split_documents(raw_documents)
        print("Chunks got splitted")
        # 2. Parallel Metadata Enrichment
        # We wrap the enrichment in tasks to run them concurrently
        enrichment_tasks = []
        for chunk in chunks:
            # Pass existing metadata (filename, page) to merge with LLM tags
            task = self.enricher.enrich_chunk(
                chunk_text=chunk.page_content, 
                source_meta=chunk.metadata
            )
            enrichment_tasks.append(task)

        # Execute all LLM tagging calls in parallel
        enriched_metadata_list = await asyncio.gather(*enrichment_tasks)

        # 3. Apply enriched metadata back to chunks
        for i, chunk in enumerate(chunks):
            chunk.metadata = enriched_metadata_list[i]

        # 4. Storage in ChromaDB
        # This will trigger the Azure Embedding model for each chunk
        vector_db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=settings.VECTOR_DB_PATH,
            collection_name="brand_guidelines"
        )

        vector_db = Chroma(
                persist_directory=settings.VECTOR_DB_PATH,
                embedding_function=self.embeddings,
                collection_name="brand_guidelines"
        )

        # DELETE the existing documents in this collection
        # This prevents the "re-appending" issue
        existing_ids = vector_db.get()["ids"]
        if existing_ids:
            vector_db.delete(ids=existing_ids)
            print(f"🗑️ Cleared {len(existing_ids)} old chunks from collection.")

        # Now add the fresh, enriched documents
        vector_db.add_documents(documents=chunks)
        
        print("Successfully saved fresh chunks to ChromaDB")
        return {"status": "success", "total_chunks": len(chunks)}
