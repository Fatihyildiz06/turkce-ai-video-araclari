/**
 * Ses cilasi: dis sesi yayin seviyesine getirir, muzigi konusma altinda otomatik kisar, karistirir.
 *
 *   node ses-cila.mjs --dis-ses public/dis-ses.wav --muzik out/muzik.wav --cikti out/miks.wav
 *   node ses-cila.mjs --dis-ses public/dis-ses.wav --cikti out/dis-ses-cilali.wav      (yalniz seviye)
 *
 * --gecikme sn : dis ses videoda bu kadar gec baslar (videodaki giris bosluguna gore)
 * --lufs  -16  : hedef seviye (web/YouTube icin -16, TV yayini icin -23)
 * --muzik-db -14 : muzigin konusmaya gore seviyesi
 */
import { execFileSync, spawnSync } from "node:child_process";

const arg = (ad, varsayilan) => {
  const i = process.argv.indexOf(`--${ad}`);
  return i > 0 ? process.argv[i + 1] : varsayilan;
};
const disSes = arg("dis-ses");
const muzik = arg("muzik");
const cikti = arg("cikti");
const lufs = Number(arg("lufs", -16));
const gecikme = Math.round(Number(arg("gecikme", 0)) * 1000);
const muzikDb = Number(arg("muzik-db", -14));
if (!disSes || !cikti) {
  console.error("Kullanim: node ses-cila.mjs --dis-ses <dosya> [--muzik <dosya>] --cikti <dosya> [--gecikme sn] [--lufs -16] [--muzik-db -14]");
  process.exit(1);
}

// loudnorm iki gecis: once olc, sonra olculen degerlerle dogrusal duzelt (tek gecis nefes aralarini pompalar).
const olc = spawnSync("ffmpeg", ["-hide_banner", "-i", disSes, "-af", `loudnorm=I=${lufs}:TP=-1.5:LRA=11:print_format=json`, "-f", "null", "-"], { encoding: "utf8" });
const o = JSON.parse(olc.stderr.slice(olc.stderr.lastIndexOf("{"), olc.stderr.lastIndexOf("}") + 1));
console.log(`dis ses: ${o.input_i} LUFS, tepe ${o.input_tp} dB -> hedef ${lufs} LUFS`);
const norm = `loudnorm=I=${lufs}:TP=-1.5:LRA=11:measured_I=${o.input_i}:measured_TP=${o.input_tp}:measured_LRA=${o.input_lra}:measured_thresh=${o.input_thresh}:offset=${o.target_offset}:linear=true`;
const ses = `[0:a]highpass=f=70,${norm},aresample=48000,adelay=${gecikme}:all=1`;

const filtre = muzik
  ? `${ses},asplit=2[d][anahtar];[1:a]aresample=48000,volume=${muzikDb}dB[m];[m][anahtar]sidechaincompress=threshold=0.03:ratio=6:attack=40:release=500[mk];[mk][d]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89[a]`
  : `${ses},alimiter=limit=0.89[a]`;

execFileSync("ffmpeg", ["-y", "-hide_banner", "-loglevel", "warning", "-i", disSes, ...(muzik ? ["-i", muzik] : []), "-filter_complex", filtre, "-map", "[a]", "-ar", "48000", cikti], { stdio: "inherit" });
console.log(`hazir: ${cikti}${muzik ? " (dis ses + kisilan muzik)" : ""}`);
