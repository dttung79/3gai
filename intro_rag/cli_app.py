#!/usr/bin/env python3
"""
CLI RAG Application using OpenAI Assistant API
Simple example demonstrating Retrieval-Augmented Generation with CLI interface
"""

import os
import sys
import argparse
import asyncio
from typing import List, Optional, Dict
from dataclasses import dataclass
from pathlib import Path

# Third-party imports
import openai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import torch

# ============================================================================
# CONFIGURATION CLASS
# ============================================================================

@dataclass
class RAGConfig:
    """Configuration for RAG CLI application"""
    # OpenAI Settings
    openai_model: str = "gpt-4o"
    assistant_name: str = "Greenwich RAG Assistant"
    assistant_instructions: str = """Bạn là trợ lý AI thông minh, giúp trả lời câu hỏi dựa trên thông tin được cung cấp.
    Hãy trả lời một cách chính xác và hữu ích bằng tiếng Việt.
    Nếu thông tin không đủ để trả lời, hãy nói rõ điều đó."""
    
    # Embedding Settings
    embedding_model: str = "BAAI/bge-m3"
    
    # Search Settings  
    top_k: int = 3
    similarity_threshold: float = 0.7
    
    # Directories
    bin_dir: str = "bins"
    chunk_dir: str = "chunks"
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not os.path.exists(self.bin_dir):
            raise FileNotFoundError(f"Binary directory not found: {self.bin_dir}")
        if not os.path.exists(self.chunk_dir):
            raise FileNotFoundError(f"Chunk directory not found: {self.chunk_dir}")

# ============================================================================
# VECTOR SEARCH CLASS
# ============================================================================

class VectorSearchEngine:
    """Simple vector search engine using FAISS"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.model: Optional[SentenceTransformer] = None
        self.indices: Dict[str, faiss.Index] = {}
        self.chunks: Dict[str, List[str]] = {}
        self.device = 'mps' if torch.backends.mps.is_available() else 'cpu'
        
    def initialize(self) -> bool:
        """Initialize the search engine"""
        print(f"🔄 Initializing vector search on {self.device}...")
        
        # Load embedding model
        try:
            self.model = SentenceTransformer(self.config.embedding_model, device=self.device)
            print(f"✅ Loaded embedding model: {self.config.embedding_model}")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            return False
            
        # Load FAISS indices and chunks
        return self._load_indices_and_chunks()
    
    def _load_indices_and_chunks(self) -> bool:
        """Load FAISS indices and corresponding text chunks"""
        try:
            loaded_count = 0
            
            for bin_file in os.listdir(self.config.bin_dir):
                if bin_file.startswith('faiss_index_') and bin_file.endswith('.bin'):
                    key = bin_file[len('faiss_index_'):-len('.bin')]
                    
                    # Load FAISS index
                    index_path = os.path.join(self.config.bin_dir, bin_file)
                    self.indices[key] = faiss.read_index(index_path)
                    
                    # Load corresponding chunks
                    chunk_file = os.path.join(self.config.chunk_dir, f'chunks_{key}.txt')
                    if os.path.exists(chunk_file):
                        with open(chunk_file, 'r', encoding='utf-8') as f:
                            self.chunks[key] = f.read().split('\n---\n')[:-1]
                        loaded_count += 1
                    else:
                        print(f"⚠️  Chunk file not found: {chunk_file}")
            
            if loaded_count == 0:
                print("❌ No data indices found!")
                return False
            else:
                print(f"✅ Loaded {loaded_count} data indices")
                return True
                
        except Exception as e:
            print(f"❌ Error loading indices: {e}")
            return False
    
    def search(self, query: str) -> List[str]:
        """Search for relevant text chunks"""
        if not self.model or not self.indices:
            print("❌ Search engine not initialized")
            return []
        
        try:
            # Encode query
            query_embedding = self.model.encode([query])
            
            # Search across all indices
            all_results = []
            for key, index in self.indices.items():
                if key in self.chunks:
                    distances, indices_found = index.search(query_embedding, k=self.config.top_k)
                    for distance, idx in zip(distances[0], indices_found[0]):
                        if idx < len(self.chunks[key]) and idx >= 0:
                            # Filter by similarity threshold
                            similarity = 1 - distance  # Convert distance to similarity
                            if similarity >= self.config.similarity_threshold:
                                all_results.append((similarity, self.chunks[key][idx]))
            
            # Sort by similarity and return top chunks
            all_results.sort(key=lambda x: x[0], reverse=True)
            return [chunk for _, chunk in all_results[:self.config.top_k]]
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []

# ============================================================================
# OPENAI ASSISTANT CLASS
# ============================================================================

class OpenAIAssistant:
    """OpenAI Assistant API wrapper"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.client: Optional[openai.OpenAI] = None
        self.assistant = None
        self.thread = None
        
    def initialize(self) -> bool:
        """Initialize OpenAI client and assistant"""
        try:
            # Initialize client
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("❌ OPENAI_API_KEY environment variable not set")
                return False
                
            self.client = openai.OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized")
            
            # Create assistant
            self.assistant = self.client.beta.assistants.create(
                name=self.config.assistant_name,
                instructions=self.config.assistant_instructions,
                model=self.config.openai_model,
            )
            print(f"✅ Created assistant: {self.assistant.id}")
            
            # Create thread
            self.thread = self.client.beta.threads.create()
            print(f"✅ Created thread: {self.thread.id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize OpenAI assistant: {e}")
            return False
    
    def get_response(self, query: str, context: str = "") -> str:
        """Get response from assistant with optional context"""
        if not self.client or not self.assistant or not self.thread:
            return "❌ Assistant not initialized"
        
        try:
            # Prepare message with context
            if context:
                message_content = f"""Context: {context}

Question: {query}

Dựa trên thông tin context ở trên, hãy trả lời câu hỏi một cách chính xác và chi tiết."""
            else:
                message_content = query
            
            # Add message to thread
            self.client.beta.threads.messages.create(
                thread_id=self.thread.id,
                role="user",
                content=message_content
            )
            
            # Create and wait for run
            run = self.client.beta.threads.runs.create_and_poll(
                thread_id=self.thread.id,
                assistant_id=self.assistant.id
            )
            
            if run.status == 'completed':
                # Get the latest message
                messages = self.client.beta.threads.messages.list(
                    thread_id=self.thread.id,
                    limit=1
                )
                return messages.data[0].content[0].text.value
            else:
                return f"❌ Run failed with status: {run.status}"
                
        except Exception as e:
            return f"❌ Error getting response: {e}"
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.client and self.assistant:
                self.client.beta.assistants.delete(self.assistant.id)
                print(f"🧹 Cleaned up assistant: {self.assistant.id}")
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")

# ============================================================================
# CLI INTERFACE CLASS  
# ============================================================================

class RAGCLIInterface:
    """Command-line interface for RAG application"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.search_engine = VectorSearchEngine(config)
        self.assistant = OpenAIAssistant(config)
        
    def initialize(self) -> bool:
        """Initialize all components"""
        print("🚀 Initializing RAG CLI Application...")
        
        # Initialize search engine
        if not self.search_engine.initialize():
            return False
            
        # Initialize assistant
        if not self.assistant.initialize():
            return False
            
        print("✅ All components initialized successfully!\n")
        return True
    
    def interactive_mode(self):
        """Run in interactive mode"""
        print("=" * 60)
        print("🎓 Greenwich RAG Assistant - Interactive Mode")
        print("=" * 60)
        print("Type 'quit', 'exit', or 'q' to exit")
        print("Type 'help' for available commands")
        print("-" * 60)
        
        try:
            while True:
                query = input("\n💬 Your question: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if query.lower() == 'help':
                    self._show_help()
                    continue
                    
                if not query:
                    print("⚠️  Please enter a question")
                    continue
                
                self._process_query(query)
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        finally:
            self.cleanup()
    
    def single_query_mode(self, query: str):
        """Process a single query"""
        print(f"🔍 Processing query: {query}")
        self._process_query(query)
        self.cleanup()
    
    def _process_query(self, query: str):
        """Process a user query with RAG"""
        print(f"\n🔍 Searching for relevant information...")
        
        # Search for relevant context
        relevant_chunks = self.search_engine.search(query)
        
        if relevant_chunks:
            print(f"✅ Found {len(relevant_chunks)} relevant chunks")
            context = "\n\n".join(relevant_chunks)
            
            # Show context (abbreviated)
            print(f"\n📚 Context preview:")
            for i, chunk in enumerate(relevant_chunks, 1):
                preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
                print(f"   {i}. {preview}")
            
            print(f"\n🤖 Generating response...")
            response = self.assistant.get_response(query, context)
        else:
            print("⚠️  No relevant information found, asking without context...")
            response = self.assistant.get_response(query)
        
        print(f"\n💡 Answer:")
        print("-" * 40)
        print(response)
        print("-" * 40)
    
    def _show_help(self):
        """Show help information"""
        print("\n📋 Available commands:")
        print("  help     - Show this help message")
        print("  quit/exit/q - Exit the application")
        print("\n💡 Example questions:")
        print("  - Học phí của trường là bao nhiêu?")
        print("  - Các ngành học tại Greenwich có gì?")
        print("  - Điều kiện đầu vào như thế nào?")
    
    def cleanup(self):
        """Clean up resources"""
        print("\n🧹 Cleaning up...")
        self.assistant.cleanup()

# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class RAGApplication:
    """Main RAG application"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.cli = RAGCLIInterface(config)
        
    def run(self, args: argparse.Namespace):
        """Run the application"""
        # Initialize components
        if not self.cli.initialize():
            print("❌ Failed to initialize application")
            sys.exit(1)
        
        # Run based on mode
        if args.query:
            # Single query mode
            self.cli.single_query_mode(args.query)
        else:
            # Interactive mode
            self.cli.interactive_mode()

# ============================================================================
# COMMAND LINE ARGUMENT PARSER
# ============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="RAG CLI Application using OpenAI Assistant API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_app.py                           # Interactive mode
  python cli_app.py -q "Học phí là bao nhiêu?" # Single query mode
  python cli_app.py --config custom_config.py  # Custom config
        """
    )
    
    parser.add_argument(
        '-q', '--query',
        type=str,
        help='Single query to process (non-interactive mode)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to custom configuration file'
    )
    
    parser.add_argument(
        '--top-k',
        type=int,
        default=3,
        help='Number of top results to retrieve (default: 3)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4o',
        help='OpenAI model to use (default: gpt-4o)'
    )
    
    return parser

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Create configuration
        config = RAGConfig()
        
        # Override config with command line arguments
        if args.top_k:
            config.top_k = args.top_k
        if args.model:
            config.openai_model = args.model
        
        # Create and run application
        app = RAGApplication(config)
        app.run(args)
        
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 