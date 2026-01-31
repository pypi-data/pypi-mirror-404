from langchain_openai import ChatOpenAI
import os
from typing import List, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()






class RAGChatbot:
    def __init__(self):
        # Chat model
        self._API_KEY = os.getenv("_API_KEY")
        self.LLM_MODEL = os.getenv("LLM_MODEL")
        self.LLM_BASE_URL = os.getenv("LLM_BASE_URL")
        self.llm = ChatOpenAI(
            
            model=self.LLM_MODEL,  # Perplexity's web-searching model
            temperature=0.1,
            # Perplexity configuration
            base_url=self.LLM_BASE_URL,
            api_key=self._API_KEY,  # Perplexity API key only
        )

       
       
        self.system_prompt = (
    "You are an expert assistant whose task is to **answer the user’s question using ONLY the provided context**\n\n"
    "IMPORTANT INSTRUCTIONS:\n"
        "1. **Use the context to generate your answer** — do not add facts or knowledge that are not supported by the context."
        "2. When you make a statement, **reference the relevant part of the context** (e.g., mention or paraphrase what the context says). You can cite context with brief mentions like: “[from context: ...]”."
        "3. If multiple context pieces support a point, **combine them logically** into the answer."
        "4. Do not say “I’m not sure” if the context has relevant information — instead, extract and rephrase the relevant parts of the context."
        "5. Only say “I’m not sure based on the provided information” **if the context has no relevant detail at all** for the specific question."
        "6. Provide clear, **structured answers** (e.g., bullet points, lists) when multiple items or examples are involved."
        "7. Avoid using information or explanations not found in the context — if you rely on a detail, explicitly reference the context snippet you used."
    "Answer the user’s question strictly based on the context provided."
)



    async def _build_context(self, docs: List[Dict]) -> str:
        """Format retrieved chunks into a single context string."""
        parts = []
        for d in docs:
            src = d.get("source", "Unknown")
            headers = d.get("headers", {})
            header_str = " | ".join(f"{k}: {v}" for k, v in headers.items())
            text = d.get("text", "")
            parts.append(f"[Source: {src} | {header_str}]\n{text}")
        return "\n\n---\n\n".join(parts)

    async def chat(self, user_query: str, retrieved_docs: List[Dict],retrieval_metrics: Dict) -> Dict:
        """
        End-to-end RAG chat:
        - retrieves context from Pinecone
        - calls ChatOpenAI with a strict system prompt
        - returns answer + some debug info
        """
        
        # print("Building context from retrieved documents...")
        # context_text = await self._build_context(retrieved_docs)
        
        # 2. Build messages for ChatOpenAI
        messages = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": (
                    "Use ONLY the following context to answer.\n\n"
                    f"CONTEXT:\n{retrieved_docs}\n\n"
                    f"QUESTION: {user_query}"
                ),
            },
        ]
        print("Sending messages to LLM...")
        # 3. Call the chat model
        # response = await self.llm.ainvoke(messages)
        # print("LLM response received.")
        # answer = response.content if hasattr(response, "content") else str(response)

        # return {
        #     "answer": answer,
        #     "retrieval_metrics": retrieval_metrics,
        #     "sources": retrieved_docs,
        # }
        print("Streaming LLM response...")

        # collect streamed output
        answer_text = ""

        # stream chunks as they’re generated
        async for chunk in self.llm.astream(messages):
            text_piece = getattr(chunk, "content", None)
            if text_piece:
                # accumulate text
                answer_text += text_piece
                # print(text_piece, end="", flush=True)

        print("\nLLM streaming complete.")

        return {
            "answer": answer_text,
            "retrieval_metrics": retrieval_metrics,
            "sources": retrieved_docs,
        }

