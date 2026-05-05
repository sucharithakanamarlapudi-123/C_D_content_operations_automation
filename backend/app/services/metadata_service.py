import json
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.config import Settings
from app.schemas.ingestion import ChunkMetadata

settings = Settings()

class MetadataEnricher:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.AZURE_OPENAI_LLM_DEPLOYMENT,
            api_version=settings.OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            temperature=0 # Use 0 for consistent tagging
        )
        
    async def enrich_chunk(self, chunk_text: str, source_meta: dict) -> dict:
        """
        Takes raw text and uses an LLM to extract structured metadata.
        """
        prompt = ChatPromptTemplate.from_template("""
            Analyze the following brand guideline snippet and extract metadata in JSON format.
            
            Fields to extract:
            - section_title: The name of the section (e.g., 'VOICE AND TONE', 'VISUAL IDENTITY')
            - rule_category: One of (Banned Word, Product Name, Channel Spec, CTA, or General)
            - audience_target: Who this rule applies to (e.g., 'Internal Developers', 'Marketing', 'General')
            - summary: A 1-sentence summary of the rule.
            
            Snippet: {text}
            
            Return ONLY the JSON object.
            JSON Output:
        """)
        
        chain = prompt | self.llm
        print("Calling the LLM to get ")
        try:
            response = await chain.ainvoke({"text": chunk_text})
        except Exception as e:
            print(e)
        print("Got the response")
        
        try:
            # 1. Clean the LLM response (sometimes they add markdown backticks)
            content = response.content.strip().replace("```json", "").replace("```", "")
            extracted = json.loads(content)

            print("Source Meta",source_meta)
            print("Extracted",extracted)            
            # 2. VALIDATION STEP: Use the Schema
            # We combine source_meta (filename/page) with the LLM output
            validated_meta = ChunkMetadata(
                source_file=source_meta.get("source", "unknown"),
                page_number=source_meta.get("page", 0),
                section_title=extracted.get("section_title", "General"),
                rule_category=extracted.get("rule_category", "General"),
                audience_target=extracted.get("audience_target", "General"),
                is_violation_rule=True # Defaulting to true for these guidelines
            )
            
            # Return as a validated dictionary
            return validated_meta.model_dump()
            
        except Exception as e:
            print(f"Metadata enrichment failed: {e}")
            # Fallback: Create a minimal valid schema object to avoid breaking the ingest
            return ChunkMetadata(
                source_file=source_meta.get("source", "unknown"),
                page_number=source_meta.get("page", 0),
                section_title="Uncategorized",
                rule_category="General",
                is_violation_rule=False
            ).model_dump()