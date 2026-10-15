# Hugging Face'ten ComfyUI model dosyalarını indirir (yarıda kalırsa kaldığı yerden sürer).
# Kullanım: python model-indir.py <grup> [grup...]   -> gruplar aşağıda
# Hedef klasör COMFY_MODELLER ortam değişkeninden okunur (ComfyUI'nin "models" klasörü).
import os, subprocess, sys, time

MODELLER = os.environ.get("COMFY_MODELLER", r"C:\ComfyUI\ComfyUI_windows_portable\ComfyUI\models")
if not os.path.isdir(MODELLER):
    sys.exit(f'Model klasörü yok: {MODELLER}\nCOMFY_MODELLER ortam değişkenine ComfyUI "models" klasörünü ver.')
CURL = "curl.exe" if os.name == "nt" else "curl"

GRUPLAR = {
    "h3": ("Comfy-Org/MiniMax-H3", [
        "vae/minimax_h3_video_vae_fp16.safetensors",
        "vae/minimax_h3_audio_vae_fp32.safetensors",
        "loras/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors",
        "loras/minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors",
        "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
        "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors",
    ]),
    "ltx": ("Lightricks/LTX-2.5", [
        "vae/ltx-2.5-video-vae-bf16.safetensors",
        "vae/ltx-2.5-video-vae-conv-bf16.safetensors",
        "vae/ltx-2.5-audio-vae-bf16.safetensors",
        "latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors",
        "latent_upscale_models/ltx-2.5-latent-temporal-upscaler-x2-bf16-1.0.safetensors",
        "text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors",
        "diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors",
    ]),
    "qwen-turbo": ("Comfy-Org/Qwen-Image-2.1", [
        "diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors",
    ]),
    "h3ref": ("Comfy-Org/MiniMax-H3", [
        "loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors",
        "diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors",
    ]),
}

# indirme sürerken bilgisayar uykuya geçmesin (yalnızca Windows, yalnızca bu süreç yaşadıkça geçerli)
if os.name == "nt":
    import ctypes
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)

if not sys.argv[1:]:
    sys.exit(f"Kullanım: python model-indir.py <grup> [grup...]\nGruplar: {', '.join(GRUPLAR)}")

for grup in sys.argv[1:]:
    depo, dosyalar = GRUPLAR[grup]
    for dosya in dosyalar:
        hedef = os.path.join(MODELLER, dosya.replace("/", os.sep))
        if os.path.exists(hedef):
            print(f"VAR    {dosya}", flush=True)
            continue
        t = time.time()
        os.makedirs(os.path.dirname(hedef), exist_ok=True)
        # hf_hub'in xet indiricisi hattı onlarca bağlantıyla boğup yavaşlıyor; tek bağlantılı curl daha hızlı
        url = f"https://huggingface.co/{depo}/resolve/main/{dosya}"
        for deneme in range(20):
            if subprocess.run([CURL, "-L", "-s", "-S", "--fail", "-C", "-", "-o", hedef + ".yarim", url]).returncode == 0:
                break
            print(f"HATA ({deneme + 1}/20) {dosya}, kaldigi yerden suruyor", flush=True)
            time.sleep(15)
        else:
            sys.exit(f"INDIRILEMEDI {dosya}")
        os.replace(hedef + ".yarim", hedef)
        gb = os.path.getsize(hedef) / 2**30
        print(f"TAMAM  {dosya}  {gb:.1f} GB  {(time.time() - t) / 60:.0f} dk", flush=True)
    print(f"GRUP BITTI {grup}", flush=True)
