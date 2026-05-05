import json
import os
from datetime import datetime
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings

class AuditorService:
    def __init__(self):
        print("Auditor service got initiated")
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.AZURE_OPENAI_LLM_DEPLOYMENT,
            api_version=settings.OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            temperature=0
        )
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            api_version=settings.OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
        )
        self.vector_db = Chroma(
            persist_directory=settings.VECTOR_DB_PATH,
            embedding_function=self.embeddings,
            collection_name="brand_guidelines"
        )
        # Ensure reports directory exists
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.reports_dir = os.path.join(base_dir, "storage", "audit_reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    async def audit_content(self, content: str):
        # 1. RAG: Retrieve relevant rules
        print("Retrieving the rules similar to the content")
        docs = self.vector_db.similarity_search(content, k=8)
        
        # 2. Build Context with Enriched Metadata for Citations
        rules_context = ""
        for d in docs:
            m = d.metadata
            rules_context += f"- [RULE]: {d.page_content}\n  [SOURCE INFO]: Section: {m.get('section_title')}, Page: {m.get('page_number')}\n\n"

        # 3. Audit Prompt
        prompt = f"""
        You are the Axion Brand Compliance Auditor. 
        Compare the 'User Content' against the 'Brand Rules' provided below.
        
        Brand Rules:
        {rules_context}

        User Content to Audit:
        {content}

        Instructions:
        - Identify violations (banned words, terminology, tone).
        - Provide a verbatim 'citation' from the rules including Section and Page info.
        - Suggest a specific correction.
        - Calculate a 'score' (0-100).

        Return ONLY a JSON object:
        {{
            "score": int,
            "summary": "string",
            "violations": [
                {{ "rule_category": "string", "issue_found": "string", "citation": "string", "suggestion": "string" }}
            ]
        }}
        """

        response = await self.llm.ainvoke(prompt)
        
        # Clean and parse response
        raw_content = response.content.strip().replace("```json", "").replace("```", "")
        audit_data = json.loads(raw_content)

        # 4. Store as .txt file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"audit_report_{timestamp}.txt"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        with open(report_path, "w") as f:
            f.write(f"--- AXION BRAND COMPLIANCE REPORT ---\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Compliance Score: {audit_data['score']}/100\n")
            f.write(f"Summary: {audit_data['summary']}\n\n")
            f.write(f"DETAILED VIOLATIONS:\n" + "-"*20 + "\n")
            for i, v in enumerate(audit_data['violations'], 1):
                f.write(f"{i}. Category: {v['rule_category']}\n   Issue: {v['issue_found']}\n   Citation: {v['citation']}\n   Suggestion: {v['suggestion']}\n\n")
        
        audit_data["report_saved_at"] = report_path
        return audit_data