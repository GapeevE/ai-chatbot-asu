import hashlib
import os
import shutil
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import MarkdownTextSplitter, RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

CHROMA_PATH = "./db_metadata_v5"
DATA_PATH = "./docs"
global_unique_hashes = set()

def walk_through_files(path, file_extension='.txt'):
    for (dir_path, dir_names, filenames) in os.walk(path):
        for filename in filenames:
            if filename.endswith(file_extension):
                yield os.path.join(dir_path, filename)

def load_documents():
    documents = []
    for f_name in walk_through_files(DATA_PATH):
        try:
            with open(f_name, "r", encoding="utf-8") as infile:
                first_line = infile.readline().strip()
                if first_line.startswith("URL: "):
                    url = first_line[5:].strip()  
                    content = infile.read() 
                    metadata = {"url": url} 
                    document = Document(page_content=content, metadata=metadata) 
                    documents.append(document)
                else:
                    print(f"Файл {f_name} не содержит URL в первой строке. Пропускаем.")
        except Exception as e:
            print(f"Ошибка при обработке файла {f_name}: {e}")
    return documents

def hash_text(text):
    hash_object = hashlib.sha256(text.encode())
    return hash_object.hexdigest()

def is_markdown(text):
    if "# " in text or "## " in text or "### " in text or "#### " in text or "##### " in text or "###### " in text or "    * " in text:
        return True
    return False

def split_text(documents: list[Document]):
    chunks = []
    for document in documents:
        if is_markdown(document.page_content):
            text_splitter = MarkdownTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                length_function=len
            )
            doc_chunks = text_splitter.split_documents([document])
            print("Создание чанков на маркдаунах - MarkdownTextSplitter")
        else:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=100,
                length_function=len,
            )
            doc_chunks = text_splitter.split_documents([document])
            print("Создание чанков - RecursiveCharacterTextSplitter")
        chunks.extend(doc_chunks)
    print(f"Разделено {len(documents)} документов на {len(chunks)} блоков.")
    unique_chunks = []
    for chunk in chunks:
        chunk_hash = hash_text(chunk.page_content)
        if chunk_hash not in global_unique_hashes:
            unique_chunks.append(chunk)
            global_unique_hashes.add(chunk_hash)
    print(f"Всего уникальных чанков: {len(unique_chunks)}.")
    return unique_chunks

def save_to_chroma(chunks: list[Document]):
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [chunk.metadata for chunk in chunks]
    db = Chroma.from_texts(
        texts=texts,
        metadatas=metadatas,
        embedding=OllamaEmbeddings(model="mxbai-embed-large"),
        persist_directory=CHROMA_PATH
    )
    db.persist()
    print(f"Сохранено {len(chunks)} чанков в '{CHROMA_PATH}'.")

def generate_data_store():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)

if __name__ == "__main__":
    generate_data_store()