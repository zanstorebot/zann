FROM python:3.12-slim

RUN apt-get update -y && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ffmpeg git neofetch apt-utils libmediainfo0v5 sqlite3 \
    libgl1-mesa-glx libglib2.0-0 libxml2-dev libxslt-dev sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt
    

COPY . .


RUN chmod +x start.sh


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 7860-8000

ENTRYPOINT ["./start.sh"]
