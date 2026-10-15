# Windows notları

Windows 11'de yerel video üretirken karşılaştığımız, hata mesajı yanıltıcı olduğu için çözmesi uzun süren sorunlar.

## 1. Smart App Control, npm'den gelen ffmpeg'i ve Chrome'u öldürüyor

**Belirti:** Remotion render'ı ya da `ffmpeg-static` gibi paketler hiçbir hata yazmadan ölüyor. Çıkış kodu `3236495362` (`0xC0E90002`), stderr boş. Remotion'ın indirdiği `chrome-headless-shell.exe` için `spawn UNKNOWN` (errno -4094) görülüyor.

**Neden:** Windows **Smart App Control** açıkken imzasız, internetten inmiş ikililer çalıştırılmıyor. CodeIntegrity günlüğünde bile iz kalmayabiliyor.

**Kontrol:**

```
reg query HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy /v VerifiedAndReputablePolicyState
```

`1` = açık, `0` = kapalı.

**Çözüm (ayarı kapatmadan):**

- Tarayıcı için sistemdeki imzalı Chrome'u verin:
  `--browser-executable="C:\Program Files\Google\Chrome\Application\chrome.exe"`
- ffmpeg için sistemde **imzalı** bir ffmpeg kullanın (ör. başka bir uygulamanın getirdiği), Remotion'dan PNG kare dizisi alıp (`--sequence --image-format=png`) kodlamayı o ffmpeg ile yapın.

Smart App Control kapatılırsa yeniden açmak için temiz Windows kurulumu gerekir. Bu bir güvenlik ayarı; kapatmadan önce iyi düşünün.

## 2. Node'dan `npx.cmd` çağırmak sessizce boş çıktı veriyor

**Belirti:** Bir build betiğinde `execFileSync("npx.cmd", [...])` → `spawnSync npx.cmd EINVAL`. Bazı durumlarda betik çıkış kodu 0 ile bitiyor ama çıktı üretilmemiş oluyor.

**Neden:** Node 18+ Windows'ta güvenlik gereği `.cmd` / `.bat` dosyalarını `shell: true` olmadan çalıştırmıyor.

**Çözüm:** CLI'nin gerçek JS girişini doğrudan Node ile çalıştırın:

```js
execFileSync(process.execPath, [
  resolve(ROOT, "node_modules/@remotion/cli/remotion-cli.js"),
  "render", id, out,
]);
```

Bu `tsc`, `eslint` gibi her npm komutu için geçerli. Ayrıca çıktı dosyasının gerçekten oluştuğunu kontrol edin.

## 3. faster-whisper GPU'da sessizce çöküyor

**Belirti:** `faster-whisper` CUDA ile başlarken hiçbir şey yazmadan kapanıyor.

**Neden:** `pip` ile gelen `nvidia-cublas` / `nvidia-cudnn` DLL'leri PATH'te değil; ctranslate2 bulamıyor.

**Çözüm:** `yaziya.py` başında `site-packages/nvidia/{cublas,cudnn}/bin` klasörlerini `os.add_dll_directory` ile ekliyor. Aynı betik sesi faster-whisper'ın kendi çözücüsü yerine ffmpeg ile açıyor, çünkü kurulu PyAV sürümüyle uyuşmazlık çıkabiliyor.

## 4. winget ffmpeg'inde `drawtext` çöküyor

winget ile kurulan ffmpeg'de `drawtext` filtresi (fontconfig yok) segmentation fault verebiliyor. Yazıyı ffmpeg yerine video aracında (Remotion vb.) basın.
