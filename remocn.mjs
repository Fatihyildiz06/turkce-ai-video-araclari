/**
 * Remocn (remocn.dev) bilesenlerini projeye kopyalar: src/remocn/<ad>.tsx
 *
 *   node remocn.mjs marker-highlight handwrite wave-wipe
 *   node remocn.mjs --liste [arama]
 *
 * Bilesenler kopyadir, bagimlilik degil: kendi renk kurallarin icin dosyayi dogrudan duzenle.
 * Bagimli oldugu baska remocn parcalarini da ceker; gereken npm paketlerini sonda listeler.
 */
import { mkdirSync, writeFileSync } from "node:fs";
import { basename, dirname, relative, resolve, sep } from "node:path";

const KAYIT = "https://remocn.dev/r";
const al = async (ad) => {
  const r = await fetch(`${KAYIT}/${ad}.json`);
  if (!r.ok) throw new Error(`Remocn'da "${ad}" yok (${r.status})`);
  return r.json();
};

const argv = process.argv.slice(2);
if (argv[0] === "--liste") {
  const { items } = await al("registry");
  const ara = argv[1]?.toLowerCase();
  for (const i of items) if (!ara || `${i.name} ${i.description ?? ""}`.toLowerCase().includes(ara)) console.log(`${i.name.padEnd(28)} ${i.description ?? ""}`);
  process.exit(0);
}
if (!argv.length) {
  console.error("Kullanim: node remocn.mjs <bilesen...> | --liste [arama]");
  process.exit(1);
}

const KOK = resolve("src/remocn");
const ic = (yol) => yol.replace(/^components\/remocn\//, "").replace(/^(components|lib)\//, "").replace(/^remocn\//, "");
const gorulen = new Set();
const paketler = new Set();
const kuyruk = [...argv];
while (kuyruk.length) {
  const ad = kuyruk.shift().replace(/^@remocn\//, "");
  if (gorulen.has(ad)) continue;
  gorulen.add(ad);
  const j = await al(ad);
  for (const p of j.dependencies ?? []) paketler.add(p);
  kuyruk.push(...(j.registryDependencies ?? []));
  for (const f of j.files) {
    // target: components/remocn/x.tsx -> src/remocn/x.tsx, lib/y/z.ts -> src/remocn/y/z.ts; "@/..." importlari goreli yapilir
    const hedef = resolve(KOK, ic(f.target ?? basename(f.path)));
    mkdirSync(dirname(hedef), { recursive: true });
    const goreli = (_, yol) => {
      const g = relative(dirname(hedef), resolve(KOK, ic(yol))).split(sep).join("/");
      return `from "${g.startsWith(".") ? g : `./${g}`}"`;
    };
    writeFileSync(hedef, f.content.replace(/^"use client";\s*/, "").replace(/from "@\/([^"]+)"/g, goreli));
    console.log(hedef);
  }
}
const disPaket = [...paketler].filter((p) => !["remotion", "react", "react-dom"].includes(p));
if (disPaket.length) console.log(`\ngereken npm paketleri: ${disPaket.join(" ")}`);
