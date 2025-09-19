# ai_engine.py (เวอร์ชันอัปเกรดสำหรับ LangChain v0.2.x)
import os
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA
# -----------------------------

# --- ตั้งค่า ---
TYPHOON_API_KEY = os.environ.get('TYPHOON_API_KEY')
FAISS_INDEX_PATH = "./faiss_index"
# ---------------

try:
    embeddings = OpenAIEmbeddings(
        model="gte-large",
        openai_api_base="https://api.opentyphoon.ai/v1",
        openai_api_key=TYPHOON_API_KEY
    )
    
    vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)

    llm = ChatOpenAI(
        model="typhoon-instruct",
        openai_api_base="https://api.opentyphoon.ai/v1",
        openai_api_key=TYPHOON_API_KEY,
        temperature=0,
        max_tokens=1024,
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(),
        return_source_documents=True
    )
    print("AI Engine (OpenTyphoon, LangChain v0.2) โหลดสำเร็จ พร้อมใช้งาน")

except Exception as e:
    print(f"!!! เกิดข้อผิดพลาดในการโหลด AI Engine: {e}")
    qa_chain = None

def get_ai_response(question: str) -> str:
    # ... (ส่วนนี้เหมือนเดิม ไม่ต้องแก้ไข) ...
    if not qa_chain:
        return "ขออภัยค่ะ ขณะนี้ระบบ AI ขัดข้อง โปรดลองใหม่อีกครั้ง"
    prompt = f"""จากข้อมูลที่ให้มาเท่านั้น โปรดตอบคำถามต่อไปนี้อย่างกระชับและตรงไปตรงมา: "{question}"
    หากข้อมูลไม่เพียงพอ ให้ตอบว่า "ฉันไม่พบข้อมูลเกี่ยวกับเรื่องนี้ในเอกสาร"
    """
    result = qa_chain.invoke({"query": prompt}) # เปลี่ยนจาก .call หรือ __call__ เป็น .invoke
    answer = result.get("result", "ไม่สามารถสร้างคำตอบได้")
    source_documents = result.get("source_documents")
    if source_documents:
        source_name = os.path.basename(source_documents[0].metadata.get("source", "ไม่พบชื่อเอกสาร"))
        return f"{answer}\n\nอ้างอิงจาก: {source_name}"
    else:
        return answer