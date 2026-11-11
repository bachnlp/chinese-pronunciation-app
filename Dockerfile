# Sử dụng base image Python 3.10 phiên bản slim gọn nhẹ
FROM python:3.10-slim

# Thiết lập thư mục làm việc bên trong container
WORKDIR /app

# Cài đặt các gói hệ thống tối thiểu cần thiết (bỏ build-essential nếu không biên dịch C)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Chỉ copy file requirements.txt trước để tận dụng Docker Cache
COPY requirements.txt .

# Cài đặt các thư viện Python (tách riêng torch bản CPU hoặc cài trực tiếp từ requirements)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn project vào container
COPY . .

# Mở cổng 8000 cho FastAPI
EXPOSE 8000

# Lệnh chạy ứng dụng khi container khởi động
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}