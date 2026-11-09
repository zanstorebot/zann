#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
[ "$(id -u)" -eq 0 ] && S="" || S="sudo"
B='\033[1;34m'; R='\033[1;31m'; G='\033[1;32m'; N='\033[0m'

echo -e "${B}Installation Your Bot\nDeveloper: alicedevscodes\nAlice Setup Started${N}"
for p in $(seq 0 100); do
  f=$((p*30/100)); s=""
  for ((i=0;i<30;i++)); do ((i<f)) && s+="█" || s+="░"; done
  printf "\r${B}[%s] %3d%%${N}" "$s" "$p"; sleep 0.05
done
echo

echo "[1/4] ffmpeg + ffprobe"
$S apt-get update -y && $S apt-get install -y ffmpeg curl python3-pip

echo "[2/4] docker + quote api"
command -v docker >/dev/null || curl -fsSL https://get.docker.com | $S sh
$S docker rm -f quotly-api >/dev/null 2>&1 || true
$S docker run -d --name quotly-api --restart always -p 3000:3000 ghcr.io/lyosu/quote-api:latest

echo "[3/4] requirements + opencv fix"
pip3 install -r requirements.txt || true
pip3 uninstall -y opencv-python-headless || true
pip3 install --upgrade opencv-python-headless

echo "[4/4] env"
cp zan.env .env

echo -e "\n${R}Alice Setup Successfully${N}\n${G}Bash X to run bot${N}"
