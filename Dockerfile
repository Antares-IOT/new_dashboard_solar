# Base image
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Copy requirements terlebih dahulu
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy semua source code
COPY . .

# Expose port (samakan dengan app kamu)
EXPOSE 5028

# Run app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5028"]