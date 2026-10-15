# Renk kurali denetimi: sari + kirmizi + yesil ayni karede olmasin (bazi kurumsal kimliklerin kurali).
# Still karelerini tarar, ihlalleri listeler. Renk araliklari asagidaki RENK sozlugunden degistirilebilir.
#
#   py renk-kontrol.py out/kare                 (klasordeki tum png/jpg)
#   py renk-kontrol.py a.png b.png --esik 0.3
#
# Bir renk, doygun piksellerin karedeki payi esigi (%) gecerse "var" sayilir.
# Ihlal varsa cikis kodu 1 -> build scriptinde kapi olarak kullanilabilir.
import argparse, glob, os, sys

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8")

ap = argparse.ArgumentParser()
ap.add_argument("yollar", nargs="+")
ap.add_argument("--esik", type=float, default=0.3, help="yuzde; rengin karedeki asgari payi")
A = ap.parse_args()

# Ton araliklari (derece). Turkuaz/mavi (165+) bilerek disarida: yesilin serbest alternatifi.
RENK = {"kirmizi": [(0, 14), (346, 360)], "sari": [(42, 66)], "yesil": [(75, 164)]}

dosyalar = []
for y in A.yollar:
    if os.path.isdir(y):
        for u in ("png", "jpg", "jpeg"):
            dosyalar += glob.glob(os.path.join(y, f"*.{u}"))
    else:
        dosyalar.append(y)
dosyalar.sort()
if not dosyalar:
    sys.exit("Goruntu bulunamadi")

ihlal = 0
for d in dosyalar:
    g = Image.open(d).convert("RGB")
    g.thumbnail((640, 640))
    h, s, v = [k.astype(np.float32) for k in np.moveaxis(np.asarray(g.convert("HSV")), 2, 0)]
    ton = h * 360 / 255
    canli = (s > 110) & (v > 90)  # soluk/koyu pikseller renk sayilmaz
    pay = {ad: 100 * sum(((ton >= a) & (ton <= b) & canli).mean() for a, b in ar) for ad, ar in RENK.items()}
    kotu = all(p >= A.esik for p in pay.values())
    ihlal += kotu
    print(f"{'IHLAL' if kotu else 'tamam'}  {os.path.basename(d):<28} " + "  ".join(f"{ad} %{p:.2f}" for ad, p in pay.items()))

print(f"\n{len(dosyalar)} kare, {ihlal} ihlal")
sys.exit(1 if ihlal else 0)
