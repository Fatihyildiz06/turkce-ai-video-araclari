# Dis sesi kelime zamanlariyla yaziya doker.
#
#   py yaziya.py public/dis-ses.wav             -> out/kelimeler.json, out/altyazi.srt
#   py yaziya.py ses.mp3 --cikti baska --model medium --nefes 0.5
#
# kelimeler.json: [[bas, bit, "kelime"], ...] (saniye) -> altyazi/animasyon kodu bunu okuyabilir.
# Sonda "nefes" listesi basilir: cumle arasi bosluklar = sahne gecisi adaylari.
import argparse, json, os, site, subprocess, sys

sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("ses")
ap.add_argument("--cikti", default="out")
ap.add_argument("--model", default="large-v3")
ap.add_argument("--dil", default="tr")
ap.add_argument("--nefes", type=float, default=0.45, help="bu saniyeden uzun bosluklar sinir adayi")
ap.add_argument("--cpu", action="store_true")
A = ap.parse_args()

# pip ile gelen cuBLAS/cuDNN dll'leri PATH'te degil; ctranslate2 bulamazsa sessizce cokuyor.
for sp in site.getsitepackages() + [site.getusersitepackages()]:
    for alt in ("cublas", "cudnn"):
        d = os.path.join(sp, "nvidia", alt, "bin")
        if os.path.isdir(d):
            os.add_dll_directory(d)
            os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]

import numpy as np
from faster_whisper import WhisperModel

# faster-whisper'in kendi cozucusu kurulu PyAV ile uyusmuyor; sesi ffmpeg ile aciyoruz.
ham = subprocess.run(["ffmpeg", "-v", "error", "-i", A.ses, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"], capture_output=True, check=True).stdout
SES = np.frombuffer(ham, dtype=np.float32)


def dok(aygit, tip):
    m = WhisperModel(A.model, device=aygit, compute_type=tip)
    seg, _ = m.transcribe(SES, language=A.dil, word_timestamps=True, vad_filter=False)
    return [(s.start, s.end, s.text.strip(), [[round(float(w.start), 2), round(float(w.end), 2), w.word.strip()] for w in s.words]) for s in seg]


denemeler = [("cpu", "int8")] if A.cpu else [("cuda", "float16"), ("cuda", "int8_float16"), ("cpu", "int8")]
for aygit, tip in denemeler:
    try:
        segs = dok(aygit, tip)
        print(f"[{A.model} / {aygit} {tip}]")
        break
    except Exception as e:
        print(f"{aygit} {tip} olmadi: {str(e)[:120]}")
else:
    sys.exit(1)

ws = [w for s in segs for w in s[3]]
os.makedirs(A.cikti, exist_ok=True)
json.dump(ws, open(os.path.join(A.cikti, "kelimeler.json"), "w", encoding="utf-8"), ensure_ascii=False)


def srt(t):
    ms = round(t * 1000)
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


with open(os.path.join(A.cikti, "altyazi.srt"), "w", encoding="utf-8") as f:
    for i, (a, b, metin, _) in enumerate(segs, 1):
        f.write(f"{i}\n{srt(a)} --> {srt(b)}\n{metin}\n\n")

for a, b, w in ws:
    print(f"{a:7.2f} {b:7.2f} {w}")

# Nefesler ses enerjisinden bulunur: large-v3 kelime bitislerini sessizligin icine uzatiyor, kelime araligina guvenilmez.
PEN = 320  # 20 ms
rms = np.sqrt((SES[: len(SES) // PEN * PEN].reshape(-1, PEN) ** 2).mean(axis=1))
sessiz = np.concatenate([[False], rms < rms.max() * 0.02, [False]])
kenar = np.flatnonzero(np.diff(sessiz.astype(np.int8)))
nefes = []
for a, b in zip(kenar[::2] * 0.02, kenar[1::2] * 0.02):
    if b - a < A.nefes or a < 0.1 or b > len(SES) / 16000 - 0.1:
        continue
    t = round(float(a + b) / 2, 2)
    i = max((k for k in range(len(ws)) if ws[k][0] < t), default=0)
    nefes.append((t, ws[i][2], ws[i + 1][2] if i + 1 < len(ws) else ""))
print(f"\nnefes (>= {A.nefes} sn):")
for t, once, sonra in nefes:
    print(f"{t:7.2f}  {once} | {sonra}")
print("SINIR adayi:", [t for t, _, _ in nefes])
print(f"tamam: {len(ws)} kelime -> {A.cikti}/kelimeler.json, altyazi.srt")
