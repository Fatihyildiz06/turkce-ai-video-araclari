/**
 * ComfyUI'yi arayuzsuz surer: is akisini (API formati) kuyruga atar, bitmesini bekler, ciktilari indirir.
 *
 *   node comfy.mjs akis/arka-plan-sil.json --yukle 1.inputs.image=resim.png --cikti public
 *   node comfy.mjs akis.json --set 6.inputs.text="bir orman yolu" --set 3.inputs.seed=42 --cikti out
 *
 * --yukle dugum.inputs.alan=dosya : dosyayi ComfyUI input klasorune yukler, alana adini yazar
 * --set   dugum.inputs.alan=deger : akistaki bir degeri degistirir
 * --ad    onek                    : indirilen dosyalara verilecek ad (onek.png, onek-2.png ...)
 *
 * API formati: ComfyUI arayuzunde Workflow > Export (API). Baska scriptten: import { calistir } from "./comfy.mjs".
 */
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { basename, extname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const ADRES = process.env.COMFY_ADRES ?? "http://127.0.0.1:8188";

const yaz = (akis, yol, deger) => {
  const [dugum, ...alan] = yol.split(".");
  if (!akis[dugum]) throw new Error(`Akista ${dugum} numarali dugum yok`);
  let o = akis[dugum];
  for (const a of alan.slice(0, -1)) o = o[a];
  o[alan.at(-1)] = deger;
};

const yukle = async (dosya, adres) => {
  const f = new FormData();
  f.append("image", new Blob([readFileSync(dosya)]), basename(dosya));
  f.append("overwrite", "true");
  const r = await fetch(`${adres}/upload/image`, { method: "POST", body: f });
  if (!r.ok) throw new Error(`Yukleme hatasi ${r.status}: ${dosya}`);
  const j = await r.json();
  return j.subfolder ? `${j.subfolder}/${j.name}` : j.name;
};

export const calistir = async (akis, { set = {}, yuklenecek = {}, cikti = "out", ad, adres = ADRES } = {}) => {
  akis = structuredClone(akis);
  for (const [yol, dosya] of Object.entries(yuklenecek)) yaz(akis, yol, await yukle(dosya, adres));
  for (const [yol, deger] of Object.entries(set)) yaz(akis, yol, deger);

  const r = await fetch(`${adres}/prompt`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ prompt: akis }) });
  const j = await r.json();
  if (!r.ok || !j.prompt_id) throw new Error(`Kuyruga alinamadi: ${JSON.stringify(j.node_errors ?? j.error ?? j)}`);

  let kayit;
  for (;;) {
    await new Promise((c) => setTimeout(c, 1000));
    kayit = (await (await fetch(`${adres}/history/${j.prompt_id}`)).json())[j.prompt_id];
    if (kayit?.status?.completed || kayit?.status?.status_str === "error") break;
  }
  if (kayit.status.status_str === "error") {
    const hata = kayit.status.messages.find((m) => m[0] === "execution_error")?.[1];
    throw new Error(`ComfyUI hatasi (${hata?.node_type}): ${hata?.exception_message}`);
  }

  mkdirSync(cikti, { recursive: true });
  const dosyalar = Object.values(kayit.outputs).flatMap((o) => Object.values(o).flat()).filter((d) => d?.filename && d.type === "output");
  const yollar = [];
  for (const [i, d] of dosyalar.entries()) {
    const v = await fetch(`${adres}/view?${new URLSearchParams({ filename: d.filename, subfolder: d.subfolder ?? "", type: d.type })}`);
    if (!v.ok) throw new Error(`Indirilemedi: ${d.filename}`);
    const hedef = resolve(cikti, ad ? `${ad}${i ? `-${i + 1}` : ""}${extname(d.filename)}` : d.filename);
    writeFileSync(hedef, Buffer.from(await v.arrayBuffer()));
    yollar.push(hedef);
  }
  return yollar;
};

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const [akisYolu, ...argv] = process.argv.slice(2);
  if (!akisYolu) {
    console.error("Kullanim: node comfy.mjs <akis.json> [--yukle d.inputs.a=dosya] [--set d.inputs.a=deger] [--cikti klasor] [--ad onek]");
    process.exit(1);
  }
  const sec = { set: {}, yuklenecek: {} };
  for (let i = 0; i < argv.length; i += 2) {
    const [k, v] = [argv[i], argv[i + 1]];
    if (k === "--cikti" || k === "--ad") sec[k.slice(2)] = v;
    else if (k === "--set" || k === "--yukle") {
      const e = v.indexOf("=");
      const deger = v.slice(e + 1);
      if (k === "--yukle") sec.yuklenecek[v.slice(0, e)] = deger;
      else sec.set[v.slice(0, e)] = deger !== "" && !isNaN(deger) ? Number(deger) : deger === "true" ? true : deger === "false" ? false : deger;
    } else {
      console.error(`Bilinmeyen secenek: ${k}`);
      process.exit(1);
    }
  }
  try {
    const t = Date.now();
    const yollar = await calistir(JSON.parse(readFileSync(akisYolu, "utf8")), sec);
    console.log(`hazir (${((Date.now() - t) / 1000).toFixed(1)} sn):\n${yollar.join("\n") || "(cikti dosyasi yok)"}`);
  } catch (e) {
    console.error(e.message);
    process.exit(1);
  }
}
