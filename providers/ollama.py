from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain.chains.combine_documents import create_stuff_documents_chain
from models.index import ChatMessage
from langchain_core.documents.base import Document

CHROMA_PATH = "./db_metadata_v5"

model = OllamaLLM(model="owl/t-lite", temperature=0.1)
embedding_function = OllamaEmbeddings(model="mxbai-embed-large")
db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)
chat_history = {}

prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
                [INST]Ты - виртуальный консультант для абитуриентов Алтайского Государственного Университета (АлтГУ).
                Твоя задача - предоставлять точные, дружелюбные и полезные ответы на русском языке, основываясь исключительно на предоставленном контексте.
                Важно: Не используй никакую другую информацию, кроме той, что содержится в контексте. 
                Если информации в контексте нет, то напиши: "По данному вопросу ничего не найдено".
                Обязательно:
                - Не используй разметку текста.
                - Будь вежлив и доброжелателен.
                - Не шути и не отклоняйся от темы.
                - Если вопрос неясен, задай уточняющий вопрос.
                - Будь лаконичен.
                - Завершай ответ позитивным напутствием для абитуриента.
                [/INST]
                [INST]Контекст: {context}[/INST]
            """
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ]
)

document_chain = create_stuff_documents_chain(llm=model, prompt=prompt_template)

async def query_rag(message: ChatMessage, session_id: str = "") -> str:
    if session_id not in chat_history:
        chat_history[session_id] = []
    print(f"Вопрос пользователя: {message.question}")

    def get_chunk_id(chunk_id, base_url):
        results = db.get(
            where={"chunk_id": chunk_id},
            include=["documents", "metadatas"]
        )
        print(results)
        if results and results["metadatas"]:
            if len(results["metadatas"]) > 0:
                metadata = results["metadatas"][0]
                if "url" in metadata and metadata["url"] == base_url:
                    return chunk_id
                else:
                    return None
            else:
                return None
        else:
            return None

    def merge_and_sort_chunk_ids(data):
        grouped_data = {}
        for chunk_ids, urls in data:
            url = urls[0]
            if url not in grouped_data:
                grouped_data[url] = []
            grouped_data[url].extend(chunk_ids)
        result = []
        for url, chunk_ids in grouped_data.items():
            sorted_chunk_ids = sorted(list(set(chunk_ids)), key=lambda x: int(x))
            result.append([[str(chunk_id) for chunk_id in sorted_chunk_ids], [url]])
        return result

    def get_chunk_by_id(chunk_ids):
        contents = []
        for chunk_id in chunk_ids:
            results = db.get(
                where={"chunk_id": chunk_id},
                include=["documents"]
            )
            if results and results["documents"]:
                contents.append(results["documents"][0])
            else:
                return None
        combined_content = "\n".join(contents)
        combined_document = Document(page_content=combined_content, metadata={})
        return combined_document

    chunk_id_list = []
    relevant_docs = db.similarity_search(message.question, k=3)
    for doc in reversed(relevant_docs):
        doc_chunk_id_list = []
        doc_url_list = []
        if "chunk_id" in doc.metadata and "url" in doc.metadata:
            chunk_id = doc.metadata.get("chunk_id")
            doc_url = doc.metadata.get("url")
            if chunk_id and doc_url:
                prevent_chunk_id = int(chunk_id) - 1
                valid_prevent_chunk_id = get_chunk_id(str(prevent_chunk_id), doc_url)
                next_chunk_id = int(chunk_id) + 1
                valid_next_chunk_id = get_chunk_id(str(next_chunk_id), doc_url)
                if valid_prevent_chunk_id:
                    doc_chunk_id_list.append(valid_prevent_chunk_id)
                doc_chunk_id_list.append(chunk_id)
                if valid_next_chunk_id:
                    doc_chunk_id_list.append(valid_next_chunk_id)
                doc_url_list.append(doc_url)
        chunk_id_list.append([doc_chunk_id_list, doc_url_list])
    sorted_chunk_id_list = merge_and_sort_chunk_ids(chunk_id_list)
    expanded_relevant_docs = []
    links = []
    for items in sorted_chunk_id_list:
        links.append(items[1][0])
        document_item = get_chunk_by_id(items[0])
        expanded_relevant_docs.append(document_item)
    docs_with_score = db.similarity_search_with_score(message.question, k=3)
    for doc, score in docs_with_score:
        print(f"Document: {doc.page_content[50:]}, Score: {score}")
    print(f"Контекст: {relevant_docs}")
    response_text = document_chain.invoke({
        "context": relevant_docs,
        "question": message.question,
        "chat_history": chat_history[session_id]
    })
    chat_history[session_id].append(HumanMessage(content=message.question))
    chat_history[session_id].append(AIMessage(content=response_text))
    if links:
        links_string = "\n".join(links)
        response_text = response_text + "\n\nПолезные ссылки:\n" + links_string
    print("Ответ сформирован")
    return response_text

async def reset_context(session_id: str = "") -> str:
    if session_id in chat_history:
        chat_history[session_id] = []
    return "Контекст сброшен!"




