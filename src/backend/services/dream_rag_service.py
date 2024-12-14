import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader

class DreamRAGService:
    def __init__(self, embedding_model: str = 'all-MiniLM-L6-v2'):
        """
        Initialize Dream RAG Service with embedding model
        """
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model
        )
        
        # Path for dream knowledge base
        self.knowledge_base_path = os.path.join(
            os.path.dirname(__file__), 
            '../../..', 
            'dream_knowledge_base'
        )
        
        # Initialize vector store
        self.vector_store = self._load_or_create_vector_store()

    def _load_or_create_vector_store(self):
        """
        Load existing vector store or create a new one from knowledge base files
        """
        try:
            # Text splitter configuration
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100
            )
            
            # Collect documents from knowledge base
            documents = []
            
            # Check if knowledge base directory exists
            if not os.path.exists(self.knowledge_base_path):
                print(f"Knowledge base directory not found: {self.knowledge_base_path}")
                return None
            
            # Iterate through text files in the knowledge base
            for filename in os.listdir(self.knowledge_base_path):
                if filename.endswith('.txt'):
                    file_path = os.path.join(self.knowledge_base_path, filename)
                    
                    # Load document
                    loader = TextLoader(file_path, encoding='utf-8')
                    docs = loader.load()
                    
                    # Split documents
                    split_docs = text_splitter.split_documents(docs)
                    documents.extend(split_docs)
            
            # Create vector store if documents exist
            if documents:
                vector_store = FAISS.from_documents(
                    documents, 
                    self.embeddings
                )
                return vector_store
            else:
                print("No documents found in knowledge base")
                return None
        
        except Exception as e:
            print(f"Error creating vector store: {e}")
            return None

    def retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve contextually relevant information
        """
        try:
            if not self.vector_store:
                return ["Default dream interpretation context"]
            
            # Perform similarity search
            results = self.vector_store.similarity_search(query, k=top_k)
            
            # Extract page content
            context = [doc.page_content for doc in results]
            
            return context
        
        except Exception as e:
            print(f"Context retrieval error: {e}")
            return ["Default dream interpretation context"]

    def augment_prompt(self, dream_description: str) -> str:
        """
        Augment prompt with retrieved context
        """
        try:
            # Retrieve relevant context
            context = self.retrieve_context(dream_description)
            
            # Construct augmented prompt
            augmented_prompt = f"""
            Dream Interpretation Context:
            {' '.join(context)}

            Dream Description:
            {dream_description}

            Provide a comprehensive, psychologically insightful interpretation
            considering the contextual knowledge and symbolic meanings.
            """
            
            return augmented_prompt
        
        except Exception as e:
            print(f"Prompt augmentation error: {e}")
            return dream_description

# Optional: Debug method to list knowledge base files
def list_knowledge_base_files(service):
    """
    List files in the knowledge base directory
    """
    try:
        print("Knowledge Base Files:")
        for filename in os.listdir(service.knowledge_base_path):
            print(filename)
    except Exception as e:
        print(f"Error listing knowledge base files: {e}")

# Example usage
def main():
    # Initialize the service
    rag_service = DreamRAGService()
    
    # Debug: list knowledge base files
    list_knowledge_base_files(rag_service)
    
    # Example dream description
    dream = "I was flying over a misty landscape"
    
    # Retrieve context
    context = rag_service.retrieve_context(dream)
    print("\nRetrieved Context:")
    for ctx in context:
        print(ctx)
    
    # Augment prompt
    augmented_prompt = rag_service.augment_prompt(dream)
    print("\nAugmented Prompt:")
    print(augmented_prompt)

if __name__ == "__main__":
    main()