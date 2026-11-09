#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
[ "$(id -u)" -eq 0 ] && S="" || S="sudo"
B='\033[1;34m'; R='\033[1;31m'; G='\033[1;32m'; N='\033[0m'; LOG=install.log; : > "$LOG"
trap 'printf "\n${R}Gagal, log: install.log${N}\n"; tail -n 15 "$LOG"' ERR
bar(){ local f=$(($1*30/100)) s="" i; for((i=0;i<30;i++)); do ((i<f)) && s+="█" || s+="░"; done; printf "\r${B}[%s] %3d%% %s${N}\033[K" "$s" "$1" "$2"; }
run(){ "$@" >>"$LOG" 2>&1; }

echo -e "${B}Installation Your Bot\nDeveloper: alicedevscodes\nAlice Setup Started${N}"
bar 0 "mulai"
run $S apt-get update -y; run $S apt-get install -y ffmpeg curl python3-pip
bar 25 "ffmpeg + ffprobe"
command -v docker >/dev/null || run bash -c "curl -fsSL https://get.docker.com | $S sh"
run $S docker rm -f quotly-api || true
run $S docker run -d --name quotly-api --restart always -p 3000:3000 ghcr.io/lyosu/quote-api:latest
bar 50 "docker + quote api"
run pip3 install -r requirements.txt || true
bar 75 "requirements"
run pip3 uninstall -y opencv-python-headless || true
run pip3 install --upgrade opencv-python-headless
bar 90 "opencv fix"
cp zann.env .env
bar 100 "selesai"
echo -e "\n${R}Alice Setup Successfully${N}\n${G}Bash X to run bot${N}"
