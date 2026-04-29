FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (needed for pg_isready and potentially some python packages)
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Create upload folder explicitly as root/app user
RUN mkdir -p /app/uploaded_images

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
