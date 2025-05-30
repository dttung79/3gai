import streamlit as st
# Must be the first Streamlit command
st.set_page_config(
    page_title="Chatbot Tuyển Sinh Greenwich - OpenAI",
    page_icon="🎓",
    layout="wide"
)

import openai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import torch
import os
from typing import Dict, List, Tuple, Optional, Generator
from dataclasses import dataclass

# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class AppConfig:
    """Application configuration settings"""
    # OpenAI Settings
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    MAX_TOKENS: int = 1000
    TEMPERATURE: float = 0.7
    
    # Embedding Settings
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    
    # Search Settings
    TOP_K: int = 5
    
    # Directories
    BIN_DIR: str = "bins"
    CHUNK_DIR: str = "chunks"
    
    # UI Settings
    PAGE_TITLE: str = "Chatbot Tuyển Sinh Greenwich - OpenAI"
    PAGE_ICON: str = "🎓"
    
    # System Prompt
    SYSTEM_PROMPT: str = """Bạn là trợ lý tư vấn tuyển sinh của trường Đại học Greenwich Việt Nam. 
    Hãy trả lời các câu hỏi dựa trên thông tin được cung cấp một cách chuyên nghiệp và thân thiện.
    Luôn trả lời bằng tiếng Việt và cung cấp thông tin chính xác, hữu ích.
    
    Nếu thông tin được cung cấp không đủ để trả lời câu hỏi, hãy nói rõ và đề xuất cách tìm hiểu thêm."""

# ============================================================================
# OPENAI CHATBOT CLASS
# ============================================================================

class OpenAIChatbot:
    """Handles OpenAI API interactions for chatbot functionality"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.client = self._init_openai_client()
    
    def _init_openai_client(self) -> openai.OpenAI:
        """Initialize OpenAI client with API key from Streamlit secrets"""
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
            if api_key == "your-openai-api-key-here":
                st.error("🔑 Vui lòng cập nhật OPENAI_API_KEY trong file .streamlit/secrets.toml")
                st.stop()
            return openai.OpenAI(api_key=api_key)
        except KeyError:
            st.error("🔑 OPENAI_API_KEY không tìm thấy trong Streamlit secrets!")
            st.stop()
        except Exception as e:
            st.error(f"❌ Lỗi khởi tạo OpenAI client: {str(e)}")
            st.stop()
    
    def get_response(self, context: str, query: str) -> str:
        """Get complete response from OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": self.config.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"Dựa trên thông tin sau:\n\n{context}\n\nTrả lời câu hỏi: {query}"
                    }
                ],
                max_tokens=self.config.MAX_TOKENS,
                temperature=self.config.TEMPERATURE
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ Lỗi khi gọi OpenAI API: {str(e)}"
    
    def get_streaming_response(self, context: str, query: str) -> Generator[str, None, None]:
        """Get streaming response from OpenAI API"""
        try:
            stream = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": self.config.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"Dựa trên thông tin sau:\n\n{context}\n\nTrả lời câu hỏi: {query}"
                    }
                ],
                max_tokens=self.config.MAX_TOKENS,
                temperature=self.config.TEMPERATURE,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"❌ Lỗi khi gọi OpenAI API: {str(e)}"

# ============================================================================
# VECTOR SEARCH MANAGER CLASS
# ============================================================================

class VectorSearchManager:
    """Manages FAISS indices and vector search operations"""
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.indices: Dict[str, faiss.Index] = {}
        self.chunks_dict: Dict[str, List[str]] = {}
        self.model = None
        self.device = self._get_device_info()
        
    def _get_device_info(self) -> str:
        """Get information about the device being used"""
        return 'mps' if torch.backends.mps.is_available() else 'cpu'
    
    def get_device_info(self) -> str:
        """Public method to get device info"""
        return self.device
    
    def _load_embedding_model(self) -> SentenceTransformer:
        """Load and cache the embedding model"""
        if self.model is None:
            with st.spinner(f"🔄 Đang tải mô hình embedding trên {self.device}..."):
                self.model = SentenceTransformer(self.config.EMBEDDING_MODEL, device=self.device)
        return self.model
    
    def _load_indices_and_chunks(self) -> bool:
        """Load FAISS indices and corresponding text chunks"""
        if not os.path.exists(self.config.BIN_DIR) or not os.path.exists(self.config.CHUNK_DIR):
            st.error(f"📁 Thư mục cần thiết không tồn tại: {self.config.BIN_DIR}, {self.config.CHUNK_DIR}")
            return False
            
        try:
            loaded_count = 0
            for bin_file in os.listdir(self.config.BIN_DIR):
                if bin_file.startswith('faiss_index_') and bin_file.endswith('.bin'):
                    key = bin_file[len('faiss_index_'):-len('.bin')]
                    
                    # Load FAISS index
                    index_path = os.path.join(self.config.BIN_DIR, bin_file)
                    self.indices[key] = faiss.read_index(index_path)
                    
                    # Load corresponding chunks
                    chunk_file = os.path.join(self.config.CHUNK_DIR, f'chunks_{key}.txt')
                    if os.path.exists(chunk_file):
                        with open(chunk_file, 'r', encoding='utf-8') as f:
                            self.chunks_dict[key] = f.read().split('\n---\n')[:-1]
                        loaded_count += 1
                    else:
                        st.warning(f"⚠️ Không tìm thấy file chunk: {chunk_file}")
            
            if loaded_count == 0:
                st.error("❌ Không tìm thấy dữ liệu chỉ mục nào!")
                return False
            else:
                st.success(f"✅ Đã tải {loaded_count} chỉ mục dữ liệu")
                return True
                        
        except Exception as e:
            st.error(f"❌ Lỗi khi tải chỉ mục và chunks: {str(e)}")
            return False
    
    def initialize(self) -> bool:
        """Initialize the search manager"""
        # Load embedding model
        self._load_embedding_model()
        
        # Load indices and chunks
        return self._load_indices_and_chunks()
    
    def encode_query(self, query: str) -> np.ndarray:
        """Encode a query string into embeddings"""
        if self.model is None:
            self._load_embedding_model()
        return self.model.encode([query])
    
    def search(self, query: str, k: Optional[int] = None) -> List[str]:
        """Search for relevant chunks based on query"""
        if k is None:
            k = self.config.TOP_K
            
        if not self.indices:
            st.warning("⚠️ Không có chỉ mục nào được tải để tìm kiếm")
            return []
        
        try:
            # Get query embedding
            query_embedding = self.encode_query(query)
            
            # Search across all indices
            all_results = []
            for key, index in self.indices.items():
                if key in self.chunks_dict:
                    distances, indices_found = index.search(query_embedding, k=k)
                    for distance, idx in zip(distances[0], indices_found[0]):
                        if idx < len(self.chunks_dict[key]) and idx >= 0:
                            all_results.append((distance, self.chunks_dict[key][idx]))
            
            # Sort by distance and return top k chunks
            all_results.sort(key=lambda x: x[0])
            return [chunk for _, chunk in all_results[:k]]
            
        except Exception as e:
            st.error(f"❌ Lỗi trong quá trình tìm kiếm: {str(e)}")
            return []

# ============================================================================
# UI COMPONENTS CLASS
# ============================================================================

class ChatInterface:
    """Handles the chat interface components"""
    
    def __init__(self, config: AppConfig):
        self.config = config
    
    def render_header(self, device_info: str) -> None:
        """Render the application header"""
        st.title(self.config.PAGE_TITLE)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.metric("🤖 AI Model", self.config.OPENAI_MODEL)
        with col2:
            st.metric("💻 Device", device_info.upper())
        with col3:
            st.metric("🔍 Top Results", self.config.TOP_K)
        
        st.markdown("---")
        st.markdown("""
        ### 💡 Gợi ý câu hỏi:
        - Học phí của trường là bao nhiêu?
        - Các ngành học tại Greenwich có gì?
        - Điều kiện đầu vào của trường như thế nào?
        - Cơ sở vật chất của trường ra sao?
        """)
    
    def render_query_form(self) -> Optional[str]:
        """Render the query input form and return the query if submitted"""
        with st.form(key='query_form'):
            user_query = st.text_area(
                "Nhập câu hỏi của bạn:",
                placeholder="Ví dụ: Học phí của trường là bao nhiêu tiền một năm?",
                help="Hãy nhập câu hỏi về tuyển sinh, học phí, chương trình học, cơ sở vật chất...",
                height=100
            )
            
            col1, col2 = st.columns([3, 1])
            with col2:
                submit_button = st.form_submit_button(
                    label='🚀 Hỏi',
                    use_container_width=True,
                    type="primary"
                )
        
        return user_query.strip() if submit_button and user_query.strip() else None
    
    def display_response(self, response: str) -> None:
        """Display a complete response"""
        with st.container():
            st.markdown("### 💬 Câu trả lời:")
            st.markdown(response)
    
    def display_streaming_response(self, response_generator: Generator[str, None, None]) -> None:
        """Display a streaming response with real-time updates"""
        response_placeholder = st.empty()
        full_response = ""
        
        with st.container():
            st.markdown("### 💬 Câu trả lời:")
            
            for chunk in response_generator:
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            # Remove cursor and show final response
            response_placeholder.markdown(full_response)
    
    def display_sources(self, chunks: List[str]) -> None:
        """Display source information"""
        if chunks:
            with st.expander("📚 Thông tin tham khảo", expanded=False):
                for i, chunk in enumerate(chunks[:3], 1):
                    st.markdown(f"**📄 Nguồn {i}:**")
                    # Show preview of chunk
                    preview = chunk[:300] + "..." if len(chunk) > 300 else chunk
                    st.text(preview)
                    st.markdown("---")

# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================

class ChatApplication:
    """Main application class that orchestrates all components"""
    
    def __init__(self):
        self.config = AppConfig()
        self.ui = ChatInterface(self.config)
        self.chatbot = None
        self.search_manager = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize application components"""
        try:
            # Initialize chatbot
            self.chatbot = OpenAIChatbot(self.config)
            
            # Initialize search manager
            self.search_manager = VectorSearchManager(self.config)
            
            # Initialize search manager (load indices and model)
            if not self.search_manager.initialize():
                st.error("❌ Không thể khởi tạo hệ thống tìm kiếm!")
                st.stop()
                
        except Exception as e:
            st.error(f"❌ Lỗi khởi tạo ứng dụng: {str(e)}")
            st.stop()
    
    def run(self):
        """Main application loop"""
        try:
            # Render UI
            device_info = self.search_manager.get_device_info()
            self.ui.render_header(device_info)
            
            # Handle user input
            user_query = self.ui.render_query_form()
            
            if user_query:
                self._process_query(user_query)
                
        except Exception as e:
            st.error(f"❌ Lỗi ứng dụng: {str(e)}")
    
    def _process_query(self, query: str):
        """Process user query and display response"""
        with st.spinner('🔍 Đang tìm kiếm thông tin liên quan...'):
            try:
                # Search for relevant context
                relevant_chunks = self.search_manager.search(query, k=self.config.TOP_K)
                
                if not relevant_chunks:
                    st.warning("⚠️ Không tìm thấy thông tin liên quan. Vui lòng thử câu hỏi khác hoặc diễn đạt khác.")
                    return
                
                # Prepare context
                context = "\n\n".join(relevant_chunks)
                
                # Get and display response
                with st.spinner('💭 Đang tạo câu trả lời...'):
                    # Choice between regular or streaming response
                    use_streaming = st.sidebar.checkbox("🔄 Streaming Response", value=True)
                    
                    if use_streaming:
                        # Streaming response
                        response_generator = self.chatbot.get_streaming_response(context, query)
                        self.ui.display_streaming_response(response_generator)
                    else:
                        # Regular response
                        response = self.chatbot.get_response(context, query)
                        self.ui.display_response(response)
                
                # Show source information
                self.ui.display_sources(relevant_chunks)
                        
            except Exception as e:
                st.error(f"❌ Lỗi xử lý câu hỏi: {str(e)}")

# ============================================================================
# SIDEBAR CONFIGURATION
# ============================================================================

def render_sidebar():
    """Render sidebar with configuration options"""
    with st.sidebar:
        st.header("⚙️ Cấu hình")
        
        st.subheader("🤖 OpenAI Settings")
        st.info(f"Model: GPT-4 Turbo")
        st.info(f"Max Tokens: 1000")
        st.info(f"Temperature: 0.7")
        
        st.subheader("🔍 Search Settings") 
        st.info(f"Top K Results: 5")
        st.info(f"Embedding Model: BGE-M3")
        
        st.markdown("---")
        st.subheader("📋 Hướng dẫn sử dụng")
        st.markdown("""
        1. Nhập câu hỏi vào ô text
        2. Nhấn nút "Hỏi" 
        3. Đợi hệ thống tìm kiếm và trả lời
        4. Xem thông tin tham khảo ở cuối
        """)
        
        st.markdown("---")
        st.caption("🎓 Greenwich University Vietnam")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Application entry point"""
    # Render sidebar
    render_sidebar()
    
    # Run main application
    app = ChatApplication()
    app.run()

if __name__ == '__main__':
    main() 