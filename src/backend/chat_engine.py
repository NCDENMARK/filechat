from typing import Dict, Optional
from config import OPENAI_CLIENT  # Reuse the shared OpenAI client

class ChatEngine:
    def __init__(self, vector_store=None):
        # Accept a shared vector_store or create new one
        if vector_store:
            self.vector_store = vector_store
        else:
            from vector_store import VectorStore
            self.vector_store = VectorStore()
        self.conversation_history = []
    
    def ask_question(self, question: str, folder_path: Optional[str] = None) -> Dict:
        """Take a question, find relevant info, ask ChatGPT, return answer
        
        Args:
            question: The user's question
            folder_path: Optional folder path to filter results to specific folder
        """
        
        # Step 1: Search for relevant chunks in our database
        search_results = self.vector_store.search(question, n_results=5, folder_path=folder_path)
        
        # Check if we found anything
        if not search_results['documents'] or not search_results['documents'][0]:
            return {
                "answer": "I couldn't find any relevant information in your documents. Please make sure you've indexed some files first.",
                "sources": [],
                "status": "no_results"
            }
        
        # Step 2: Extract the text chunks and source files
        context_chunks = search_results['documents'][0]
        sources = []
        
        for metadata in search_results['metadatas'][0]:
            source = metadata.get('file_name', 'Unknown')
            if source not in sources:
                sources.append(source)
        
        # Step 3: Combine all chunks into one context string
        context = "\n\n".join(context_chunks)
        
        # Step 4: Create the prompt for ChatGPT
        system_prompt = (
            "You are a helpful assistant that answers questions based on the provided "
            "document context. Always base your answers on the provided context. "
            "If the answer isn't in the context, say so. Be concise but thorough."
        )
        
        user_prompt = f"""Context from documents:
{context}

Question: {question}

Please answer the question based on the context provided above."""
        
        try:
            # Step 5: Call ChatGPT API
            response = OPENAI_CLIENT.chat.completions.create(
                model="gpt-3.5-turbo",  # Stable chat model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            # Extract the answer
            answer = response.choices[0].message.content
            
            return {
                "answer": answer,
                "sources": sources,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "answer": f"Error calling OpenAI API: {str(e)}",
                "sources": [],
                "status": "error"
            }