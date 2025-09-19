# prepare_documents.py (The Ultimate Version: Local Embedding + Smart Update)
import os
import pytesseract
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings # <--- ใช้ Local Embedding
from langchain_unstructured import UnstructuredLoader

# --- ส่วนที่ 1: ตั้งค่า ---
# !!! ตรวจสอบให้แน่ใจว่าที่อยู่ Tesseract นี้ถูกต้องสำหรับเครื่องของคุณ !!!
pytesseract.pytesseract.tesseract_cmd = r'D:\my-super-bot\tesseract.exe'

DOCUMENTS_DIR = "./documents" 
FAISS_INDEX_PATH = "./faiss_index"
PROCESSED_FILES_LOG = "./processed_files.log" # สมุดบันทึกสำหรับ Smart Update
# --------------------------

def get_processed_files():
    """อ่านรายชื่อไฟล์ที่เคยประมวลผลไปแล้วจากสมุดบันทึก"""
    if not os.path.exists(PROCESSED_FILES_LOG):
        return set()
    with open(PROCESSED_FILES_LOG, 'r', encoding='utf-8') as f:
        return set(f.read().splitlines())

def add_file_to_log(filename):
    """จดชื่อไฟล์ใหม่ลงในสมุดบันทึก"""
    with open(PROCESSED_FILES_LOG, 'a', encoding='utf-8') as f:
        f.write(filename + '\n')

def prepare_vector_db():
    # --- ใช้ HuggingFaceEmbeddings เพื่อโหลด "พจนานุกรม AI" ---
    print("กำลังโหลด 'พจนานุกรม AI' (Embedding Model)... นี่อาจใช้เวลาสักครู่ในครั้งแรก")
    model_name = "intfloat/multilingual-e5-large"
    embeddings = HuggingFaceEmbeddings(model_name=model_name)
    print("'พจนานุกรม AI' โหลดสำเร็จแล้ว")
    # -------------------------------------------------------------

    # --- Logic ใหม่: ค้นหาเฉพาะไฟล์ใหม่ ---
    all_docs_in_folder = set(os.listdir(DOCUMENTS_DIR))
    processed_docs = get_processed_files()
    new_docs_to_process = sorted(list(all_docs_in_folder - processed_docs))
    # ------------------------------------

    if not new_docs_to_process and os.path.exists(FAISS_INDEX_PATH):
        print(">>> ไม่มีเอกสารใหม่ให้อัปเดต ทุกอย่างเป็นปัจจุบันแล้ว")
        return

    # ถ้าไม่มีไฟล์ใหม่เลย และยังไม่มี faiss_index (เช่น โฟลเดอร์ documents ว่าง) ก็ไม่ต้องทำอะไร
    if not new_docs_to_process:
         print(">>> ไม่พบเอกสารให้ประมวลผล")
         return

    newly_processed_texts = []
    print(f"พบเอกสารใหม่/ที่ยังไม่เคยประมวลผล {len(new_docs_to_process)} ไฟล์...")

    for file in new_docs_to_process:
        file_path = os.path.join(DOCUMENTS_DIR, file)
        if os.path.isfile(file_path):
            try:
                print(f"  - กำลังประมวลผลไฟล์: {file}")
                loader = UnstructuredLoader(
                    file_path, strategy="hi_res", languages=["tha", "eng"]
                )
                documents = loader.load()
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
                texts = text_splitter.split_documents(documents)
                newly_processed_texts.extend(texts)
                print(f"    -> แบ่งได้ {len(texts)} ส่วนย่อย")
                add_file_to_log(file) 
            except Exception as e:
                print(f"    !!! ไม่สามารถอ่านไฟล์ {file} ได้: {e}")
    
    # --- Logic ใหม่: ต่อเติมสมอง AI ---
    if os.path.exists(FAISS_INDEX_PATH):
        print("\nกำลังโหลดสมอง AI เก่าเพื่อทำการต่อเติม...")
        vectorstore = FAISS.load_local(
            FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True
        )
        vectorstore.add_documents(newly_processed_texts)
        print("ต่อเติมข้อมูลใหม่เข้าสู่สมอง AI เรียบร้อยแล้ว")
    else:
        print("\nไม่พบสมอง AI เก่า กำลังสร้างขึ้นมาใหม่ทั้งหมด...")
        vectorstore = FAISS.from_documents(newly_processed_texts, embeddings)
    
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"สร้าง/อัปเดตสมอง AI (faiss_index) เวอร์ชันล่าสุดเรียบร้อยแล้ว!")
    # -----------------------------------

# เรียกใช้ฟังก์ชันหลักโดยตรง
prepare_vector_db()