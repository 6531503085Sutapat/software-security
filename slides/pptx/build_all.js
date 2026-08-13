const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const FA = require("react-icons/fa");

const OUT = __dirname;                       // slides/pptx
const SLIDES = path.join(OUT, "..");         // slides
const REPO = path.join(SLIDES, "..");        // repo root
const LOGO = path.join(OUT, "assets", "logo-small.png");

// ---- KOSEN-KMITL CI ----
// Light theme — white background, dark text, KMITL orange + KOSEN blue accents.
const BG = "FFFFFF", PANEL = "F1F5F9", PANEL2 = "E8EDF3";
const TEXT = "1F2937", MUTED = "64748B";
const ORANGE = "E35205";   // KMITL main (Pantone 166c)
const BLUE = "017BC4";     // KOSEN
const RED = "DC2626";      // danger/attacker (strong red for white bg)
const HEAD = "Arial", BODY = "Calibri";
const shadow = () => ({ type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.12 });

async function iconPng(Comp, color) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color, size: "256" }));
  return "image/png;base64," + (await sharp(Buffer.from(svg)).png().toBuffer()).toString("base64");
}

// Estimate how many lines a string wraps to inside a box of a given width, so fixed-height
// boxes can be sized from real wrapped-line counts instead of raw item counts — a mispredicted
// single-line assumption is what let long bullets spill outside their panel.
function wrapLines(text, widthIn, fontPt) {
  const charWidthIn = (fontPt * 0.52) / 72; // empirical avg glyph width, Calibri/Arial body text
  const charsPerLine = Math.max(10, Math.floor(widthIn / charWidthIn));
  return Math.max(1, Math.ceil(text.length / charsPerLine));
}

// ---- tiny markdown helpers ----
// Protect `code span` contents from the bold/italic regexes below — a literal "*" inside
// backticks (e.g. `Resource:"*"` or `*** panic ***`) is not emphasis syntax and must survive
// verbatim; without this guard the italic regex eats asterisks out of inline code.
const strip = (s) => {
  const codeSpans = [];
  s = s.replace(/`([^`]+)`/g, (_, code) => {
    codeSpans.push(code);
    return "@@CS" + (codeSpans.length - 1) + "@@";
  });
  s = s
    .replace(/\*\*([^*]+)\*\*/g, "$1")      // **bold** -> bold
    .replace(/\*([^*\s][^*]*?)\*/g, "$1")  // *italic* -> italic
    .replace(/\*\*/g, "")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .trim();
  return s.replace(/@@CS(\d+)@@/g, (_, i) => codeSpans[Number(i)]);
};

function parseDeck(md) {
  // drop YAML front-matter
  md = md.replace(/^---\n[\s\S]*?\n---\n/, "");
  const blocks = md.split(/\n---\n/).map((b) => b.trim()).filter(Boolean);
  return blocks.map(parseBlock);
}

function parseBlock(block) {
  const lines = block.split("\n");
  let title = "", h1 = "", sub = "", author = "";
  const body = [], notes = [];
  let inCode = false, code = [], inComment = false;
  for (let raw of lines) {
    const line = raw.replace(/\s+$/, "");
    if (line.startsWith("```")) {
      if (inCode) { body.push({ t: "code", v: code.join("\n") }); code = []; inCode = false; }
      else inCode = true;
      continue;
    }
    if (inCode) { code.push(raw); continue; }
    // HTML comments (<!-- ... -->) become PowerPoint speaker notes
    if (inComment) {
      if (line.includes("-->")) { notes.push(line.replace("-->", "").trim()); inComment = false; }
      else notes.push(line.trim());
      continue;
    }
    if (line.trim().startsWith("<!--")) {
      let c = line.trim().slice(4);
      if (c.includes("-->")) notes.push(c.replace("-->", "").trim());
      else { notes.push(c.trim()); inComment = true; }
      continue;
    }
    if (line.startsWith("# ")) { h1 = strip(line.slice(2)); continue; }
    if (line.startsWith("## ")) { title = strip(line.slice(3)); continue; }
    if (!line.trim()) continue;
    body.push({ t: "raw", v: line });
  }
  if (inCode && code.length) body.push({ t: "code", v: code.join("\n") });
  return { h1, title, body, notes: notes.filter(Boolean).join(" ").trim() };
}

// classify body into renderables: bullets[], numbered[], table[][], quote, paras[], code
function organize(body) {
  const out = [];
  let i = 0;
  while (i < body.length) {
    const item = body[i];
    if (item.t === "code") { out.push({ kind: "code", text: item.v }); i++; continue; }
    const line = item.v;
    if (line.includes("|") && line.trim().startsWith("|")) {
      const rows = [];
      while (i < body.length && body[i].t === "raw" && body[i].v.trim().startsWith("|")) {
        const cells = body[i].v.split("|").slice(1, -1).map((c) => strip(c));
        if (!cells.every((c) => /^-+:?$|^:?-+$|^:?-+:?$|^$/.test(c.replace(/\s/g, "")))) rows.push(cells);
        i++;
      }
      out.push({ kind: "table", rows });
      continue;
    }
    if (/^[-*]\s+/.test(line)) {
      const items = [];
      while (i < body.length && body[i].t === "raw" && /^\s*[-*]\s+/.test(body[i].v)) {
        const lvl = /^\s{2,}/.test(body[i].v) ? 1 : 0;
        items.push({ text: strip(body[i].v.replace(/^\s*[-*]\s+/, "")), lvl });
        i++;
      }
      out.push({ kind: "bullets", items });
      continue;
    }
    if (/^\d+\.\s+/.test(line)) {
      const items = [];
      while (i < body.length && body[i].t === "raw" && /^\d+\.\s+/.test(body[i].v)) {
        items.push(strip(body[i].v.replace(/^\d+\.\s+/, ""))); i++;
      }
      out.push({ kind: "numbered", items });
      continue;
    }
    if (line.startsWith(">")) {
      const q = [];
      while (i < body.length && body[i].t === "raw" && body[i].v.startsWith(">")) { q.push(strip(body[i].v.replace(/^>\s?/, ""))); i++; }
      out.push({ kind: "quote", text: q.join(" ") });
      continue;
    }
    const paras = [];
    while (i < body.length && body[i].t === "raw" && !body[i].v.includes("|") && !/^[-*]\s+/.test(body[i].v) && !/^\d+\.\s+/.test(body[i].v) && !body[i].v.startsWith(">")) {
      paras.push(strip(body[i].v)); i++;
    }
    if (paras.length) out.push({ kind: "para", text: paras.join("\n") });
  }
  return out;
}

(async () => {
  const ICON = await iconPng(FA.FaChevronRight, "#0E1726"); // dark, sits on orange circle

  for (let n = 1; n <= 19; n++) {
    const ww = String(n).padStart(2, "0");
    // Optional: WEEK=01 (or WEEK=1) rebuilds just one deck; otherwise all 19.
    if (process.env.WEEK && process.env.WEEK !== ww && process.env.WEEK !== String(n)) continue;
    const file = path.join(SLIDES, `week${ww}.md`);
    if (!fs.existsSync(file)) { console.log("skip", ww); continue; }
    const md = fs.readFileSync(file, "utf8");
    const blocks = parseDeck(md);
    const headerMatch = md.match(/header:\s*"([^"]+)"/);
    const deckLabel = headerMatch ? headerMatch[1] : `Software Security · Week ${n}`;

    const pres = new pptxgen();
    pres.layout = "LAYOUT_16x9";
    pres.author = "Nutthakorn Chalaemwongwan";
    pres.title = deckLabel;

    const base = () => { const s = pres.addSlide(); s.background = { color: BG }; return s; };
    const foot = (s, label) => {
      s.addText(deckLabel + (label ? " · " + label : ""), { x: 0.5, y: 5.25, w: 7.6, h: 0.3, fontSize: 9, color: MUTED, fontFace: BODY, margin: 0 });
      s.addImage({ path: LOGO, x: 8.62, y: 5.14, w: 0.84, h: 0.39 });
    };
    const header = (s, title) => {
      s.addShape(pres.shapes.OVAL, { x: 0.5, y: 0.42, w: 0.58, h: 0.58, fill: { color: ORANGE }, shadow: shadow() });
      s.addImage({ data: ICON, x: 0.65, y: 0.57, w: 0.28, h: 0.28 });
      s.addText(title, { x: 1.25, y: 0.36, w: 8.2, h: 0.66, fontSize: 26, bold: true, color: TEXT, fontFace: HEAD, valign: "middle", margin: 0 });
    };

    // ---- title slide (block 0) ----
    const t0 = blocks[0];
    let s = base();
    s.addImage({ path: LOGO, x: 0.7, y: 0.55, w: 1.85, h: 0.74 });
    s.addText((t0.h1 || `Week ${n}`).toUpperCase(), { x: 0.7, y: 1.95, w: 8.5, h: 0.5, fontSize: 18, bold: true, color: ORANGE, fontFace: HEAD, charSpacing: 3, margin: 0 });
    s.addText(t0.title || deckLabel, { x: 0.66, y: 2.45, w: 8.7, h: 1.5, fontSize: 40, bold: true, color: TEXT, fontFace: HEAD, lineSpacingMultiple: 0.98, margin: 0 });
    const authorLine = (t0.body.find((b) => b.t === "raw") || {}).v || "Software Security";
    s.addText(strip(authorLine), { x: 0.7, y: 4.2, w: 8.5, h: 0.4, fontSize: 14, color: MUTED, fontFace: BODY, margin: 0 });
    if (t0.notes) s.addNotes(t0.notes);

    // ---- content slides ----
    for (let bi = 1; bi < blocks.length; bi++) {
      const blk = blocks[bi];
      const items = organize(blk.body);
      s = base();
      const titleTxt = blk.title || blk.h1 || "";

      // big-statement slide: an h1 with little/no body (e.g. "# Questions?")
      if (!blk.title && blk.h1 && items.length <= 1) {
        s.addText(blk.h1, { x: 0.7, y: 1.9, w: 8.6, h: 1.2, fontSize: 46, bold: true, color: TEXT, fontFace: HEAD, margin: 0 });
        if (items[0]) s.addText(items[0].text || (items[0].items && items[0].items.map(x=>x.text).join("  ·  ")) || "", { x: 0.72, y: 3.1, w: 8.6, h: 0.8, fontSize: 18, color: ORANGE, fontFace: BODY, margin: 0 });
        s.addImage({ path: LOGO, x: 8.62, y: 5.14, w: 0.84, h: 0.39 });
        if (blk.notes) s.addNotes(blk.notes);
        continue;
      }

      header(s, titleTxt);
      let y = 1.45;
      const bottom = 5.0;
      // A block that doesn't fit on one slide gets a "(cont.)" continuation slide instead of
      // silently dropping items — the old fixed-budget loop just stopped early with no overflow
      // handling, which deleted real content (e.g. a lab's last numbered steps) with no trace.
      const pages = [s];
      const newPage = () => {
        foot(s, "");
        s = base();
        header(s, titleTxt + " (cont.)");
        pages.push(s);
        y = 1.45;
      };
      const bulletH = (b) => 0.34 + Math.max(0, wrapLines(b.text, 8.4 - (b.lvl ? 0.65 : 0.4), 14) - 1) * 0.22;
      const numberedH = (t) => Math.max(0.42, 0.28 * wrapLines(t, 8.3, 13.5) + 0.16);

      for (const it of items) {
        if (it.kind === "table") {
          if (y > bottom - 0.6) newPage();
          const rows = it.rows;
          const colN = Math.max(...rows.map((r) => r.length));
          const tbody = rows.map((r, ri) => {
            while (r.length < colN) r.push("");
            return r.map((c) => ({ text: c, options: { fontSize: ri === 0 ? 12.5 : 12, bold: ri === 0, color: ri === 0 ? "0E1726" : TEXT, fill: { color: ri === 0 ? ORANGE : (ri % 2 ? PANEL : PANEL2) }, align: "left", valign: "middle", margin: [3, 6, 3, 6] } }));
          });
          const rowH = Math.min(0.46, (bottom - y) / rows.length);
          s.addTable(tbody, { x: 0.5, y, w: 9.0, rowH, border: { type: "solid", pt: 1, color: BG } });
          y += rows.length * rowH + 0.2;
        } else if (it.kind === "code") {
          if (y > bottom - 0.6) newPage();
          // Count wrapped lines per source line too — a long unbroken command can wrap inside
          // the fixed-width box even though the source has a single "\n"-delimited line.
          const ln = it.text.split("\n").reduce((sum, l) => sum + wrapLines(l || " ", 8.4, 11.5), 0);
          const h = Math.min(0.24 * ln + 0.3, bottom - y);
          s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 9.0, h, rectRadius: 0.06, fill: { color: "0A1020" }, line: { color: PANEL2, width: 1 } });
          s.addText(it.text, { x: 0.7, y: y + 0.08, w: 8.6, h: h - 0.16, fontSize: 11.5, color: "9FE7D6", fontFace: "Courier New", valign: "top", margin: 0, fit: "shrink" });
          y += h + 0.18;
        } else if (it.kind === "bullets") {
          // Height from real wrapped-line counts per bullet, not raw bullet count — a bullet
          // long enough to wrap to 2 lines was previously charged the same 0.34in as a 1-liner,
          // which let text spill below the panel. Bullets that don't fit at all spill onto a
          // continuation slide instead of being silently dropped.
          let idx = 0;
          while (idx < it.items.length) {
            if (y > bottom - 1.0) newPage();
            let h = 0.3, count = 0;
            for (let k = idx; k < it.items.length; k++) {
              const bh = bulletH(it.items[k]);
              if (count > 0 && y + h + bh > bottom) break;
              h += bh; count++;
            }
            const chunk = it.items.slice(idx, idx + count);
            const boxH = Math.min(h, bottom - y);
            s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 9.0, h: boxH, rectRadius: 0.08, fill: { color: PANEL }, shadow: shadow() });
            s.addText(chunk.map((b) => ({ text: b.text, options: { bullet: { code: "2022" }, indentLevel: b.lvl, color: TEXT, breakLine: true, paraSpaceAfter: 6 } })),
              { x: 0.8, y: y + 0.12, w: 8.4, h: boxH - 0.24, fontSize: 14, color: TEXT, fontFace: BODY, valign: "top", margin: 0, fit: "shrink" });
            y += boxH + 0.18;
            idx += count;
          }
        } else if (it.kind === "numbered") {
          // Every item gets placed somewhere — if one doesn't fit in the remaining space, start
          // a continuation slide first rather than truncating the list (numbering carries over).
          for (let k = 0; k < it.items.length; k++) {
            const rh = numberedH(it.items[k]);
            if (y + rh > bottom - 0.1) newPage();
            s.addShape(pres.shapes.OVAL, { x: 0.55, y, w: 0.42, h: 0.42, fill: { color: ORANGE } });
            s.addText(String(k + 1), { x: 0.55, y, w: 0.42, h: 0.42, fontSize: 15, bold: true, color: "0E1726", align: "center", valign: "middle", fontFace: HEAD, margin: 0 });
            s.addText(it.items[k], { x: 1.15, y, w: 8.3, h: rh, fontSize: 13.5, color: TEXT, fontFace: BODY, valign: "middle", margin: 0, fit: "shrink" });
            y += rh + 0.08;
          }
        } else if (it.kind === "quote") {
          if (y > bottom - 0.6) newPage();
          const lines = wrapLines(it.text, 8.4, 14);
          const h = Math.min(Math.max(0.9, 0.3 * lines + 0.3), bottom - y);
          s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 9.0, h, rectRadius: 0.08, fill: { color: PANEL2 } });
          s.addText(it.text, { x: 0.8, y, w: 8.4, h, fontSize: 14, italic: true, color: ORANGE, fontFace: BODY, valign: "middle", margin: 0, fit: "shrink" });
          y += h + 0.18;
        } else if (it.kind === "para") {
          if (y > bottom - 0.6) newPage();
          const lines = it.text.split("\n").reduce((sum, l) => sum + wrapLines(l || " ", 8.8, 14), 0);
          const h = Math.min(0.3 * lines + 0.3, bottom - y);
          s.addText(it.text, { x: 0.6, y, w: 8.8, h, fontSize: 14, color: TEXT, fontFace: BODY, valign: "top", margin: 0, fit: "shrink" });
          y += h + 0.1;
        }
      }
      foot(s, "");
      if (blk.notes) pages.forEach((pg) => pg.addNotes(blk.notes));
    }

    const outFile = path.join(OUT, `week${ww}.pptx`);
    await pres.writeFile({ fileName: outFile });
    console.log("wrote", `week${ww}.pptx`, `(${blocks.length} slides)`);
  }
})();
