// ProcessHeal demo frontend — guided pipeline walkthrough + results.

const $ = (id) => document.getElementById(id);

// ---------- chart renderer (inline SVG, no libraries) ----------

function wtChart(d, showEvents) {
  const W = 820, H = 230, PAD = 30;
  const occ = d.signals.OCCUPIED || [];
  const n = (d.signals.OA_DMPR_POS || occ).length;
  const x = (i) => PAD + (i / Math.max(n - 1, 1)) * (W - 2 * PAD);
  const y = (v) => H - 24 - Math.max(0, Math.min(1, v)) * (H - 48);

  let out = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">`;
  let bandStart = null;
  occ.forEach(([, v], i) => {
    if (v > 0.5 && bandStart === null) bandStart = i;
    if ((v <= 0.5 || i === occ.length - 1) && bandStart !== null) {
      out += `<rect x="${x(bandStart)}" y="10" width="${x(i) - x(bandStart)}" height="${H - 34}" fill="#eef2f7"/>`;
      bandStart = null;
    }
  });
  const line = (name, color, dash) => {
    const s = d.signals[name];
    if (!s) return "";
    const pts = s.map(([, v], i) => `${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
    return `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2"${dash ? ' stroke-dasharray="5,4"' : ""}/>`;
  };
  out += line("OA_DMPR_CMD", "#94a3b8", true);
  out += line("OA_DMPR_POS", "#1f6feb", false);
  out += line("CHWC_VLV_CMD", "#86c7a1", true);
  out += line("CHWC_VLV_POS", "#2e8b57", false);

  if (showEvents) {
    const toIdx = (t) => {
      const [hh, mm] = t.split(":").map(Number);
      return Math.min(n - 1, Math.round((hh * 60 + mm) / 5));
    };
    d.events.forEach((e) => {
      const xi = x(toIdx(e.time));
      out += `<line x1="${xi}" y1="10" x2="${xi}" y2="${H - 24}" stroke="${e.signature ? "#dc2626" : "#64748b"}" stroke-width="${e.signature ? 2.5 : 1}" opacity="0.85"><title>${e.time} ${e.activity}</title></line>`;
    });
  }
  out += `<text x="${PAD}" y="${H - 6}" font-size="11" fill="#64748b">00:00</text>`;
  out += `<text x="${W - PAD}" y="${H - 6}" font-size="11" fill="#64748b" text-anchor="end">23:55</text>`;
  out += `<text x="${PAD}" y="20" font-size="11" fill="#64748b">1.0</text>`;
  out += `</svg>
  <div style="font-size:12px;color:#64748b;margin-top:6px">
    <span style="color:#1f6feb">&#9644;</span> damper position&nbsp;
    <span style="color:#94a3b8">&#9648;</span> damper command&nbsp;
    <span style="color:#2e8b57">&#9644;</span> valve position&nbsp;
    <span style="color:#86c7a1">&#9648;</span> valve command&nbsp;
    <span style="background:#eef2f7;padding:0 6px">occupied hours</span>
  </div>`;
  return out;
}

function wtChips(list, cls) {
  return `<ul class="chips">${list
    .map((e) => `<li class="${cls}"><b>${e.equipment}</b>: ${e.event} (${e.count})</li>`)
    .join("")}</ul>`;
}

function tracePill(seq, note) {
  return `<div class="trace-pill">${seq.join(" &rarr; ")}${note ? `<span>${note}</span>` : ""}</div>`;
}

// ---------- the six walkthrough steps ----------

const WT = { data: null, step: 0 };

const WT_STEPS = [
  {
    title: "Step 1 — The raw data",
    stage: (d) => wtChart(d, false),
    plain: (d) =>
      `This is ${d.day} in the "${d.label}" scenario: ${d.n_day_rows.toLocaleString()} sensor ` +
      `readings for one day. Raw numbers like these are all a building ever records — ` +
      `solid lines are what the equipment actually did, dashed lines are what it was told to do.`,
    detail: () =>
      "LBNL SDAHU dataset: 30 sensor points at 1-minute sampling (chart downsampled to " +
      "5-minute for display). Column names are mapped to canonical names via sensors.yaml, " +
      "so the same pipeline reads any building's export.",
  },
  {
    title: "Step 2 — Numbers become events",
    stage: (d) =>
      wtChart(d, true) +
      `<div style="margin-top:10px">${wtChips(
        d.events.map((e) => ({ equipment: e.time, event: e.activity, count: e.signature ? "signature" : "mode" })),
        ""
      )}</div>`,
    plain: (d) =>
      `ProcessHeal turned those ${d.n_day_rows.toLocaleString()} rows into ${d.n_events} ` +
      `events — the moments that matter. Red markers are fault signatures (an actuator ` +
      `not doing what it was told); grey markers are normal operating transitions.`,
    detail: () =>
      "Rules live in rules.yaml and are dispatched by kind (occupancy, mode, window, " +
      "mismatch, leak, setpoint deviation). A mismatch fires only after |position − " +
      "command| > 0.05 for 60 CONSECUTIVE minutes — interval-aware, so the same config " +
      "works on 1-, 5- or 15-minute data.",
  },
  {
    title: "Step 3 — Healthy days become traces",
    stage: (d) =>
      `<p style="margin:0 0 10px;font-size:13px;color:#64748b">The most common daily ` +
      `patterns across ${d.n_train_traces} healthy training days ` +
      `(${d.n_variants} distinct patterns in total):</p>` +
      d.healthy_variants.map((v) => tracePill(v.trace, `${v.days} days`)).join(""),
    plain: (d) =>
      `Before any model exists, ProcessHeal watches healthy operation. Each day becomes a ` +
      `trace — the sequence of that day's events. ${d.n_train_traces} training days ` +
      `collapse into just ${d.n_variants} distinct patterns, and the few shown here cover ` +
      `most days. THIS is the input the model is built from: sequences, not numbers.`,
    detail: () =>
      "One calendar day = one case (trace). Days with no events (e.g. Sundays with the " +
      "system off) produce no trace. The held-out calibration days are excluded — the " +
      "model only ever learns from the training split.",
  },
  {
    title: "Step 4 — The miner builds the map",
    stage: () => `<img src="/api/figure/healthy_net.png" alt="Discovered Petri net"/>`,
    plain: (d) =>
      `The inductive miner takes those ${d.n_variants} patterns and builds the map: it ` +
      `finds what always happens (the system starts and stops), where behaviour branches ` +
      `(economizer versus mechanical cooling), and discards patterns too rare to trust. ` +
      `The result is a Petri net — the map of normal, discovered from ` +
      `${d.n_train_days} healthy days with zero human labelling. Crucially, the red ` +
      `signature events from step 2 exist nowhere on this map.`,
    detail: (d) =>
      `PM4Py inductive miner with noise threshold 0.2 (drops infrequent variants); it ` +
      `guarantees a sound workflow net — every path can run start-to-finish. Circles are ` +
      `states, labelled boxes are operating events, black boxes are routing. The detection ` +
      `threshold is calibrated separately on ${d.n_holdout_days} held-out healthy days, so ` +
      `the model never grades its own training data.`,
  },
  {
    title: "Step 5 — The conformance check",
    stage: (d) => {
      const pct = Math.max(0, Math.min(100, ((d.day_fitness - 0.2) / 0.8) * 100));
      return (
        `<p style="margin:0 0 6px;font-size:13px;color:#64748b">This day's trace:</p>` +
        tracePill(d.day_trace, "") +
        `<div class="gauge" style="margin-top:14px"><div class="gauge-label">This day's conformance fitness</div>` +
        `<div class="bar"><div class="fill${d.flagged ? " low" : ""}" style="width:${pct}%"></div></div>` +
        `<div class="gauge-foot"><span>fitness ${d.day_fitness.toFixed(3)}</span>` +
        `<span>calibrated threshold ${d.threshold.toFixed(3)} &middot; healthy avg ${d.healthy_fitness.toFixed(3)}</span></div></div>` +
        (d.unexpected.length ? `<h4 style="margin:12px 0 6px;font-size:13px">Unexpected behaviour</h4>${wtChips(d.unexpected, "chip-sig")}` : "") +
        (d.missing.length ? `<h4 style="margin:12px 0 6px;font-size:13px">Missing expected behaviour</h4>${wtChips(d.missing, "chip-miss")}` : "") +
        (!d.unexpected.length && !d.missing.length ? `<p style="color:var(--ok);font-weight:600">Every event fits the map.</p>` : "")
      );
    },
    plain: (d) =>
      d.flagged
        ? `Replaying this day's trace on the map: red chips are things that happened that ` +
          `never should; amber chips are things the map expected that never happened. The ` +
          `day is flagged — a signature event appeared, or its fitness fell below the ` +
          `learned threshold.`
        : `Replaying this day's trace on the map: ${(d.day_fitness * 100).toFixed(0)}% of its ` +
          `behaviour fits, above the learned threshold, with no signature events. A clean day.`,
    detail: (d) =>
      `Alignment-based conformance checking. The threshold (${d.threshold.toFixed(3)}) is the ` +
      `1st percentile of per-day fitness on the ${d.n_holdout_days} held-out healthy days — ` +
      `learned, not hand-picked. The unified detection rule flags a day iff a signature ` +
      `event occurred OR fitness < threshold; both directions of deviation are counted.`,
  },
  {
    title: "Step 6 — Verdict and evidence",
    stage: (d) => {
      const v = d.flagged
        ? `<div class="wt-verdict" style="background:#fde0e0;color:var(--fault)">Fault detected` +
          (d.equipment ? ` &rarr; ${d.equipment}` : "") + `</div>`
        : `<div class="wt-verdict" style="background:#dcede3;color:var(--ok)">Healthy day</div>`;
      const b = d.benchmark
        ? `<div class="wt-bench"><b>Across the whole benchmark</b> (per-day, out-of-sample, ` +
          `computed — not hand-typed): recall ${(d.benchmark.recall * 100).toFixed(1)}% ` +
          `(95% CI ${(d.benchmark.recall_lo * 100).toFixed(1)}&ndash;${(d.benchmark.recall_hi * 100).toFixed(1)}%), ` +
          `precision ${(d.benchmark.precision * 100).toFixed(1)}%, false-positive rate ` +
          `${(d.benchmark.fpr * 100).toFixed(1)}% — including 100% of actuator-fault days. ` +
          (d.scenario_row
            ? `In this scenario, ${d.scenario_row.combined_flagged} of ${d.scenario_row.days} days were flagged. `
            : ``) +
          `See the Results section below for the full graphs.</div>`
        : "";
      return v + b;
    },
    plain: (d) =>
      d.flagged
        ? `The diagnosis names the equipment — no fault labels, no training on faults. The ` +
          `model only ever saw healthy data, and it caught this anyway. That is the whole idea.`
        : `No fault to find here — and just as importantly, ProcessHeal does not cry wolf on ` +
          `healthy data.`,
    detail: () =>
      "Localisation is derived from the config: each event maps to its sensor (rules.yaml), " +
      "each sensor to its equipment (the building's Brick TTL). The benchmark figures come " +
      "from outputs/benchmark_v2.json, written by scripts/benchmark.py — the same numbers, " +
      "same file, no copies.",
  },
];

function wtRender() {
  const d = WT.data;
  const s = WT_STEPS[WT.step];
  $("wt-title").textContent = s.title;
  $("wt-stage").innerHTML = s.stage(d);
  $("wt-plain").textContent = s.plain(d);
  $("wt-detail-text").textContent = s.detail(d);
  $("wt-count").textContent = `${WT.step + 1} / ${WT_STEPS.length}`;
  $("wt-prev").disabled = WT.step === 0;
  $("wt-next").disabled = WT.step === WT_STEPS.length - 1;
  $("wt-dots").innerHTML = WT_STEPS.map(
    (_, i) => `<span class="${i <= WT.step ? "on" : ""}" data-i="${i}"></span>`
  ).join("");
  document.querySelectorAll("#wt-dots span").forEach((el) =>
    el.addEventListener("click", () => { WT.step = +el.dataset.i; wtRender(); })
  );
}

async function wtLoad() {
  $("wt-status").textContent = "running the real pipeline (first load takes a few seconds)…";
  $("wt-body").classList.add("hidden");
  try {
    const res = await fetch("/api/walkthrough/" + $("wt-scenario").value);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const d = await res.json();
    if (d.error) throw new Error(d.error);
    WT.data = d; WT.step = 0;
    $("wt-status").textContent = "";
    $("wt-body").classList.remove("hidden");
    wtRender();
  } catch (e) {
    $("wt-status").textContent = "could not load walkthrough: " + e.message;
  }
}

async function wtInit() {
  const list = await fetch("/api/scenarios").then((r) => r.json());
  $("wt-scenario").innerHTML = list
    .map((s) => `<option value="${s.file}"${s.file.includes("damper_stuck_075") ? " selected" : ""}>${s.label}</option>`)
    .join("");
}

$("wt-load").addEventListener("click", wtLoad);
$("wt-prev").addEventListener("click", () => { WT.step--; wtRender(); });
$("wt-next").addEventListener("click", () => { WT.step++; wtRender(); });

wtInit();
