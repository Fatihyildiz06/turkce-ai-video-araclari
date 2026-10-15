# Türkçe AI Video Araçları

Yerel bilgisayarda yapay zekâ ile video üretmek için kullandığımız araçlar. İçinde **ComfyUI iş akışları**, ComfyUI'yi komut satırından süren küçük bir istemci ve dış ses için yardımcı betikler var. Ses, yazıya dökme, seviye ayarı ve taslak seslendirme Türkçe odaklı.

Hepsi Windows 11 + NVIDIA ekran kartında, gerçek video işlerinde kullanılarak oturdu. Karşılaştığımız Windows sorunlarının çözümleri [WINDOWS-NOTLARI.md](WINDOWS-NOTLARI.md) içinde.

> *English summary at the bottom.*

## İçindekiler

| Dosya | Ne yapar |
| --- | --- |
| [`comfy.mjs`](comfy.mjs) | ComfyUI'ye arayüzsüz iş gönderir, bitmesini bekler, çıktıyı indirir. Başka betikten `import { calistir }` ile de çağrılır. |
| [`akis/`](akis) | 15 hazır ComfyUI iş akışı (API formatı): görsel üretme, düzenleme, arka plan silme, görselden video, kare çoğaltma. |
| [`model-indir.py`](model-indir.py) | Akışların istediği büyük modelleri Hugging Face'ten indirir; yarıda kalırsa kaldığı yerden sürer. |
| [`yaziya.py`](yaziya.py) | Dış sesi kelime zamanlarıyla yazıya döker (faster-whisper), SRT altyazı çıkarır, nefes aralarını sahne geçişi adayı olarak listeler. |
| [`taslak-ses.py`](taslak-ses.py) | Senaryodan taslak Türkçe dış ses üretir (Edge TTS). Gerçek seslendirme gelene kadar kurguyu oturtmak için. |
| [`ses-cila.mjs`](ses-cila.mjs) | Dış sesi yayın seviyesine (-16 LUFS) getirir, müziği konuşma altında otomatik kısar, karıştırır. |
| [`renk-kontrol.py`](renk-kontrol.py) | Karelerde yasaklı renk üçlüsü (sarı + kırmızı + yeşil) var mı diye bakar; kurumsal renk kuralları için. |
| [`remocn.mjs`](remocn.mjs) | [remocn.dev](https://remocn.dev) Remotion bileşenlerini projeye kopyalar. |

## Kurulum

- [Node.js](https://nodejs.org) 20+ (`comfy.mjs`, `ses-cila.mjs`, `remocn.mjs`)
- Python 3.10+ ve `pip install -r requirements.txt` (`yaziya.py`, `taslak-ses.py`, `renk-kontrol.py`)
- `ffmpeg` PATH'te olmalı
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) (portable sürüm yeterli), varsayılan adres `127.0.0.1:8188`. Başka adres için `COMFY_ADRES` ortam değişkeni.

## ComfyUI akışlarını çalıştırma

```
node comfy.mjs <akis.json> [--yukle düğüm.inputs.alan=dosya] [--set düğüm.inputs.alan=değer] [--cikti klasör] [--ad önek]
```

- `--yukle`: dosyayı ComfyUI'ye yükler ve akıştaki alana adını yazar.
- `--set`: akıştaki bir değeri değiştirir (istem, tohum, boyut...).
- Kendi akışınızı eklemek için ComfyUI'de **Workflow > Export (API)** ile kaydedip `akis/` içine koymanız yeterli.

Örnekler:

```
node comfy.mjs akis/gorsel-zimage.json --set 4.inputs.text="yağmurlu bir İstanbul sokağı, gece" --cikti out --ad sokak
node comfy.mjs akis/gorsel-duzenle-qwen.json --yukle 9.inputs.image=sokak.png --set 4.inputs.prompt="aynı sokak, karlı" --cikti out --ad sokak-kar
node comfy.mjs akis/video-wan-i2v-hizli.json --yukle 1.inputs.image=sokak.png --set 4.inputs.text="kamera yavaşça ilerler" --cikti out --ad sokak
node comfy.mjs akis/kare-doldur.json --yukle 1.inputs.file=sokak.mp4 --set 5.inputs.fps=32 --cikti out --ad sokak-32
node comfy.mjs akis/arka-plan-sil.json --yukle 1.inputs.image=karakter.png --cikti out --ad karakter-seffaf
```

### Akışlar

Üretim akışlarında istem `4.inputs.text` ya da `4.inputs.prompt`, tohum `6.inputs.seed`, boyut `5.inputs.width/height`. Süreler bizim makinemizde ölçüldü, sizde farklı olabilir.

| Akış | Ne yapar | Not |
| --- | --- | --- |
| `gorsel-qwen.json` | Metinden görsel (Qwen Image 2.1) | 25 adım, kare başı ~26 sn |
| `gorsel-qwen-hizli.json` | Metinden görsel (Qwen Image 2.1 Turbo) | 8 adım, ~9 sn, kalite yakın |
| `gorsel-zimage.json` | Metinden görsel (Z-Image Turbo) | |
| `gorsel-krea.json` | Metinden görsel (Krea 2 Turbo) | |
| `gorsel-duzenle-qwen.json` | Referans görseli koruyarak düzenleme | Sahneler arası karakter/mekân tutarlılığı için |
| `gorsel-img2img-zimage.json` | Kısmi yeniden çizim | `6.inputs.denoise` ~0.4–0.5 |
| `gorsel-kontrol-zimage.json` | Canny çizgisine kilitli yeniden çizim (Z-Image + Fun ControlNet Union 2.1) | 3D render'ı gerçekçileştirmek için; `denoise=1` ışığı baştan çizer, `0.8` korur |
| `arka-plan-sil.json` | Arka plan silme (BiRefNet), şeffaf PNG | |
| `kare-doldur.json` | FILM ile kare sayısını katlar | `5.inputs.fps` = kaynak fps × çarpan |
| `video-wan-i2v.json` / `-hizli` | Görselden 5 sn video (Wan 2.2), 1280×720, 16 fps | 20 / 4 adım; uzunluk `6.inputs.length` = 16×sn+1 |
| `video-h3-i2v.json` / `-hizli` | Görselden sesli video (MiniMax H3), 1344×768, 24 fps | 20 adım ~16 dk / 8 adım ~7 dk (5 sn) |
| `video-h3-r2v-hizli.json` | İki referanstan (karakter + mekân) video | Duvardaki yazı/çerçeveleri bozabiliyor |
| `video-ltx-i2v.json` | Görselden video (LTX-2.5) | **Denenmedi**: model Hugging Face'te lisans onayı istiyor |

H3 akışlarında uzunluk `4.inputs.length` kare cinsinden ve 17k+5 olmalı: 5 sn = 124, 10 sn = 243. 15 sn klip çok uzun sürüyor; 5–10 sn ile çalışmak daha verimli.

### Modeller

Model dosyaları bu repoda **yok**; her modelin kendi lisansı var, indirmeden önce kontrol edin. MiniMax H3, LTX-2.5 ve Qwen Turbo için:

```
set COMFY_MODELLER=C:\ComfyUI\ComfyUI_windows_portable\ComfyUI\models
python model-indir.py h3 h3ref ltx qwen-turbo
```

Diğerleri (Qwen Image 2.1, Z-Image Turbo, Krea 2, Wan 2.2, BiRefNet, FILM) ComfyUI'nin **Templates** menüsündeki şablonlar açılınca indirilebiliyor. Akışların beklediği dosya adları JSON'ların içinde (`unet_name`, `clip_name`, `vae_name`, `lora_name`).

## Ses araçları

```
py yaziya.py dis-ses.wav                       # -> out/kelimeler.json, out/altyazi.srt, nefes listesi
py taslak-ses.py senaryo.txt dis-ses.wav --ses tr-TR-AhmetNeural
node ses-cila.mjs --dis-ses dis-ses.wav --muzik muzik.wav --gecikme 1 --cikti miks.wav
```

- `yaziya.py` varsayılan olarak `large-v3` modelini önce CUDA'da, olmazsa CPU'da dener. `--cpu` ile doğrudan CPU.
- `ses-cila.mjs` iki geçişli `loudnorm` kullanır (tek geçiş nefes aralarını pompalar); müzik sidechain ile konuşma altında kısılır.

## Renk kontrolü

```
py renk-kontrol.py out/kareler --esik 0.3
```

Bir karede sarı, kırmızı ve yeşilin üçü birden belirgin oranda varsa `IHLAL` yazar ve 1 ile çıkar; render betiğinde kapı olarak kullanılabilir. Renk aralıkları dosyanın başındaki `RENK` sözlüğünde.

## Lisans

Kod ve akışlar [MIT](LICENSE). Akışların kullandığı modeller kendi lisanslarına tabidir.

---

## English summary

Tools we use to produce AI-assisted videos locally on Windows + NVIDIA:

- **`comfy.mjs`**: headless ComfyUI client (queue an API-format workflow, override inputs with `--set`, upload files with `--yukle`, download outputs).
- **`akis/`**: 15 ComfyUI API workflows: text-to-image (Qwen Image 2.1, Z-Image Turbo, Krea 2), image editing, ControlNet re-render, background removal, frame interpolation (FILM), image-to-video (Wan 2.2, MiniMax H3, LTX-2.5).
- **`model-indir.py`**: resumable Hugging Face model downloader (`COMFY_MODELLER` = your ComfyUI `models` folder).
- **Audio helpers**: word-level Turkish transcription + SRT + pause detection (`yaziya.py`), draft Turkish TTS (`taslak-ses.py`), two-pass loudness normalisation with music ducking (`ses-cila.mjs`).
- **[WINDOWS-NOTLARI.md](WINDOWS-NOTLARI.md)**: fixes for Windows pitfalls (Smart App Control killing bundled ffmpeg/Chrome, `npx.cmd` spawn EINVAL in Node, faster-whisper CUDA DLLs).

Script comments and CLI flags are in Turkish; issues and PRs in English are welcome.
