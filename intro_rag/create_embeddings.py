from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import torch
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from extract_text import extract_text_from_file

# Chọn thiết bị: MPS nếu có, nếu không thì CPU
device = 'mps' if torch.backends.mps.is_available() else 'cpu'
print(f"Sử dụng thiết bị: {device}")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, chunk_overlap=50, length_function=len, separators=["\n\n", "\n", " ", ""]
)

# Tải mô hình
model = SentenceTransformer('BAAI/bge-m3')

# Thư mục chứa tài liệu và file bin
doc_dir = 'docs'
bin_dir = 'bins'
chunk_dir = 'chunks'

# Xử lý từng tài liệu
for file_name in os.listdir(doc_dir):
    print(f"Xử lý tài liệu: {file_name}")
    file_path = os.path.join(doc_dir, file_name)
    if file_name.endswith('.pdf') or file_name.endswith('.docx'):
        # Trích xuất và chia nhỏ văn bản (dùng code trước)
        text = extract_text_from_file(file_path)
        chunks = text_splitter.split_text(text)
        
        # Tạo embeddings
        embeddings = model.encode(chunks, show_progress_bar=True, batch_size=32)
        
        # Tạo FAISS index cho tài liệu này
        dimension = embeddings.shape[1]  # 1024 với bge-m3
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings))
        
        # Lưu vào file riêng
        bin_file = os.path.join(bin_dir, f'faiss_index_{file_name}.bin')
        faiss.write_index(index, bin_file)
        
        # Lưu chunks riêng (nếu cần)
        chunk_file = os.path.join(chunk_dir, f'chunks_{file_name}.txt')
        with open(chunk_file, 'w', encoding='utf-8') as f:
            for chunk in chunks:
                f.write(chunk + '\n---\n')

    print(f"Xong {file_name}!")