# Dockerfile (เวอร์ชัน All-in-One - สมบูรณ์ที่สุด)

# --- STAGE 1: Builder ---
# สเตจนี้มีหน้าที่แค่ดาวน์โหลดโค้ดและ LFS ให้เสร็จ
FROM python:3.11-slim as builder

# ติดตั้ง Git และ LFS
RUN apt-get update && apt-get install -y --no-install-recommends git git-lfs && apt-get clean

WORKDIR /app

# โคลน Repository
RUN git clone --depth 1 https://github.com/Trolli-sys/Line-OA-V2.git .

# เปิดใช้งานและดึงไฟล์ LFS
RUN git lfs install
RUN git lfs pull


# --- STAGE 2: Runner ---
# สเตจนี้คือ "บ้าน" ที่จะให้บริการจริง
FROM python:3.11-slim

# ติดตั้ง Tesseract และ Poppler
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-tha \
    poppler-utils \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# คัดลอก "ผลลัพธ์" ทั้งหมดจากสเตจแรกเข้ามา
# (ตอนนี้จะมีโค้ด + สมอง AI ที่ดาวน์โหลดเสร็จแล้ว)
COPY --from=builder /app .

# ติดตั้งไลบรารี Python
RUN pip install --no-cache-dir -r requirements.txt

# ตั้งค่า Port ที่ Render ต้องการ
EXPOSE 10000

# คำสั่งเปิดร้านสุดท้าย
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]