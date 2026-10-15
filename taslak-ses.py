# Senaryodan taslak dis ses uretir (Microsoft Edge TTS, internet gerekir).
# Gercek seslendirme gelene kadar kurguyu oturtmak icin; teslimde kullanilmaz.
#
#   py taslak-ses.py senaryo.txt public/dis-ses.wav
#   py taslak-ses.py senaryo.txt public/dis-ses.wav --ses tr-TR-AhmetNeural --hiz -5%
#
# Senaryodaki "|" ve "*" isaretleri (vurgu/bolme isaretleri) okunmadan once temizlenir.
import argparse, asyncio, os, re, subprocess, sys, tempfile

import edge_tts

sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("senaryo")
ap.add_argument("cikti")
ap.add_argument("--ses", default="tr-TR-EmelNeural", help="tr-TR-EmelNeural (kadin) / tr-TR-AhmetNeural (erkek)")
ap.add_argument("--hiz", default="+0%")
A = ap.parse_args()

metin = re.sub(r"[|*]", "", open(A.senaryo, encoding="utf-8").read())
metin = re.sub(r"[ \t]+", " ", metin).strip()

mp3 = os.path.join(tempfile.gettempdir(), "taslak-ses.mp3")
asyncio.run(edge_tts.Communicate(metin, A.ses, rate=A.hiz).save(mp3))
os.makedirs(os.path.dirname(os.path.abspath(A.cikti)), exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", mp3, "-ar", "44100", "-ac", "1", A.cikti], check=True)
sure = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", A.cikti], capture_output=True, text=True).stdout.strip()
print(f"hazir: {A.cikti} ({float(sure):.1f} sn, {A.ses})")
