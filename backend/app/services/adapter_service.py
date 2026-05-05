import json
import os
from datetime import datetime
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings
from app.core.prompts import ADAPTER_PROMPTS

class AdapterService:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment=settings.AZURE_OPENAI_LLM_DEPLOYMENT,
            api_version=settings.OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            temperature=0.7 # Higher temperature for creative adaptation
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

    async def adapt_content(self, source_content: str, channel: str, target_audience: str):
        # 1. Fetch relevant brand rules for the source content
        relevant_rules = self.vector_db.similarity_search(source_content, k=5)
        rules_text = "\n".join([f"- {d.page_content}" for d in relevant_rules])

        # 2. Get channel-specific DNA
        channel_config = ADAPTER_PROMPTS.get(channel.lower())
        if not channel_config:
            raise ValueError(f"Channel {channel} not supported.")

        # 3. The "Master Adapter" Prompt
        prompt = f"""
        You are an expert Content Strategist. Your goal is to adapt 'Source Content' into a '{channel}' for a '{target_audience}' audience.

        [SOURCE CONTENT]:
        {source_content}

        [BRAND RULES]:
        {rules_text}

        [CHANNEL SPECIFIC RULES]:
        {channel_config['rules']}
        [CHANNEL TONE]:
        {channel_config['tone']}

        TASK:
        1. Rewrite the content for the target channel.
        2. Ensure ALL Brand Rules are followed (e.g., no banned words).
        3. Create a MANDATORY Change Log documenting every major linguistic or structural change.

        Return ONLY a JSON object:
        {{
            "channel": "{channel}",
            "target_audience": "{target_audience}",
            "adapted_content": "The full adapted text here",
            "change_log": [
                {{ "original_element": "quote/fact from source", "adapted_element": "new version", "rationale": "why" }}
            ],
            "brand_compliance_check": "How you ensured brand alignment"
        }}
        """

        response = await self.llm.ainvoke(prompt)
        data = json.loads(response.content.strip().replace("```json", "").replace("```", ""))

        # 4. Persistence: Store the artifact
        self._save_artifact(data, channel)
        return data

    def _save_artifact(self, data, channel):
        os.makedirs("storage/artifacts", exist_ok=True)
        filename = f"artifact_{channel}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(f"storage/artifacts/{filename}", "w") as f:
            json.dump(data, f, indent=4)
