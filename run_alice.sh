#!/bin/bash

if ! docker image inspect alice > /dev/null 2>&1; then
  echo "🔧 Image 'alice' tidak ditemukan. Membangun image terlebih dahulu..."
  docker build . -t alice
  if [ $? -ne 0 ]; then
    echo "❌ Gagal membangun image 'alice'."
    exit 1
  fi
  echo "✅ Image 'alice' berhasil dibangun."
else
  echo "✅ Image 'alice' sudah ada."
fi

PORT=$(python3 -c "
import socket
p = next((p for p in range(7860, 7960) if socket.socket().connect_ex(('localhost', p)) != 0), None)
print(p)
")

if [ -z "$PORT" ]; then
  echo "❌ Tidak ada port kosong antara 7860-7959. Gagal menjalankan."
  exit 1
fi

echo "✅ Port kosong ditemukan: $PORT"

docker run --name alice -p ${PORT}:${PORT} -d -t alice

echo "🚀 Container 'alice' sudah jalan di port ${PORT}"
