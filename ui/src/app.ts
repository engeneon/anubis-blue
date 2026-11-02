import { mvpScope, requirementsRows, requirementsText } from "./projection-summary.js";
import { projectionSummary, projectionSummaryText, projectionGrammarVersion } from "./projection-summary.js";
import { mountCopilot, mountConnections } from "./copilot.js";
import { mountGuided, architectureView } from "./guided.js";
import { mountDiscovery } from "./discovery.js";
import { lookupHelp, quantityHelp, phaseGuidance, type FieldHelp } from "./help.js";
type J = Record<string, any>;
type RecordEntity = {
  id: string;
  type: string;
  case_id: string;
  workflow?: J;
  version: number;
  data: J;
};
const app = document.querySelector<HTMLDivElement>("#app")!;
let currentCase: RecordEntity | null = null,
  draft: RecordEntity | null = null,
  result: RecordEntity | null = null,
  stories: J[] = [],
  cases: RecordEntity[] = [],
  phase = 0,
  selectedStage = 0,
  tab = "cases",
  dirty = false,
  runToken = 0;
const phases = [
  "Purpose",
  "Composition",
  "Models",
  "Demand",
  "Service",
  "Data",
  "Operations",
  "Review",
];
const types = [
  "inference",
  "batch",
  "training",
  "transfer",
  "data",
  "checkpoint",
  "cpu",
  "unsupported",
];
const units = [
  "count",
  "request/s",
  "request/min",
  "token",
  "s",
  "ms",
  "hour",
  "day",
  "ratio",
  "percent",
  "B",
  "GB",
  "TB",
  "GiB",
  "TiB",
  "PiB",
  "B/s",
  "GB/s",
  "GiB/s",
  "Gbps",
  "ops/s",
];
let planningCatalog: J = {};
let advancedEditor = false;
let guidedEntryStep = 0;
let fields: J = {};
let phaseFields: J = {};
let chosenActivation: string | null = null;
let activeProfiles: J[] = [];
function useActivation(record: RecordEntity) {
  chosenActivation = record.id;
  activeProfiles = record.data.knowledge_lock.resolved.profiles;
}
function el<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  cls = "",
  text = "",
): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  e.className = cls;
  e.textContent = text;
  return e;
}
function notice(message: string) {
  const n = document.querySelector<HTMLDivElement>("#notice")!;
  n.textContent = message;
  n.style.display = "block";
  window.setTimeout(() => (n.style.display = "none"), 6500);
}
async function api(
  path: string,
  method = "GET",
  body?: unknown,
  version?: number,
): Promise<any> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (version) headers["If-Match"] = String(version);
  if (method === "POST") headers["Idempotency-Key"] = crypto.randomUUID();
  const r = await fetch("/api/v1/" + path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok)
    throw new Error(
      `${data.error?.code || r.status}: ${data.error?.message || "Request failed"}${data.error?.path ? " · " + data.error.path : ""}`,
    );
  return data;
}
function button(
  label: string,
  action: () => void | Promise<void>,
  primary = false,
) {
  const b = el("button", primary ? "primary" : "", label);
  b.type = "button";
  b.onclick = async () => {
    b.disabled = true;
    try {
      await action();
    } catch (e) {
      notice((e as Error).message);
    } finally {
      b.disabled = false;
    }
  };
  return b;
}
function fieldGuidance(wrap: HTMLElement, label: string, control?: HTMLElement, copy?: FieldHelp) {
  const h = copy || lookupHelp(label);
  if (!h) return;
  const description = el("p", "field-definition", h[0]);
  description.id = "help-" + crypto.randomUUID();
  control?.setAttribute("aria-describedby", description.id);
  const labelElement = wrap.querySelector("label");
  if (labelElement) labelElement.title = `${h[0]} Why: ${h[1]} Example: ${h[2]}`;
  const details = el("details", "field-help");
  const summary = el("summary", "", "Why this matters and example");
  summary.setAttribute("aria-label", "Help for " + label);
  summary.title = h[0];
  details.append(summary, el("p", "", h[1]), el("p", "", "Example: " + h[2]));
  wrap.append(description, details);
}
function renderJourney(main: HTMLElement) {
  const current = tab === "cases" ? 0 : tab === "workload" ? 1 : tab === "analysis" ? 2 : 3;
  const box = el("section", "journey");
  box.setAttribute("aria-label", "From customer story to AI Factory architecture");
  box.append(el("h2", "", "Your path to an AI Factory design"), el("p", "", "Describe the workload → calculate its resource requirements → pass supported inputs and the companion brief to your downstream AI Factory design tool or process."));
  const list = el("ol", "journey-flow");
  const labels = ["Customer story", "Describe workload", "Calculate requirements", "Design handoff", "Architecture review"];
  const descriptions = ["Purpose and scope", "Application and essential measurements", "GPU, memory, storage and traffic", "Existing intake plus companion brief", "Architect reviews the returned design"];
  labels.forEach((label, i) => {
    const item = el("li", i === current ? "current" : "");
    if (i === current) item.setAttribute("aria-current", "step");
    if (i === 3 && tab === "analysis" && result) item.append(button("4. Design handoff", () => {tab="handoff";render();window.scrollTo(0,0);}));
    else item.append(el("strong", "", `${i + 1}. ${label}`));
    item.append(el("span", "", descriptions[i]));
    if (i === current) item.append(el("span", "here", "You are here"));
    list.append(item);
  });
  box.append(list, el("p", "journey-note", "Planning estimates guide architecture. measured service performance and final design approval remain explicit validation steps. Position indicates your current screen, not completion or approval."));
  main.append(box);
}
function input(
  label: string,
  value: string,
  onchange: (v: string) => void,
  type = "text",
) {
  const wrap = el("div", "field");
  const l = el("label", "", label);
  const x = el("input");
  x.id = "field-" + crypto.randomUUID();
  l.htmlFor = x.id;
  x.type = type;
  x.value = value;
  x.oninput = () => onchange(x.value);
  wrap.append(l, x);
  fieldGuidance(wrap, label, x);
  return wrap;
}
function select(
  label: string,
  value: string,
  values: string[],
  change: (v: string) => void,
) {
  const wrap = el("div", "field");
  const l = el("label", "", label);
  const x = el("select");
  x.id = "field-" + crypto.randomUUID();
  l.htmlFor = x.id;
  for (const v of values) {
    const profile=label==="Architecture profile"?planningCatalog?.architectures?.find((a:J)=>a.id===v):null;
    const o = el("option", "", profile?`${profile.platform.replace("HGX_","HGX ")} GPUs · ${profile.fabric} network · ${profile.family.replace("Enterprise RA dual plane","Enterprise reference design with two network planes")}`:v);
    o.value = v;
    o.selected = v === value;
    x.append(o);
  }
  x.onchange = () => change(x.value);
  wrap.append(l, x);
  fieldGuidance(wrap, label, x);
  return wrap;
}
function area(label: string, value: string, change: (v: string) => void) {
  const w = el("div", "field"),
    l = el("label", "", label),
    x = el("textarea");
  x.id = "field-" + crypto.randomUUID();
  l.htmlFor = x.id;
  x.value = value;
  x.oninput = () => change(x.value);
  w.append(l, x);
  fieldGuidance(w, label, x);
  return w;
}
function panel(title: string) {
  const p = el("section", "panel");
  p.append(el("h2", "", title));
  return p;
}
function badge(value: string) {
  return el("span", "badge " + value, value);
}
function mark() {
  dirty = true;
  const state = document.querySelector("#savestate");
  if (state) state.textContent = "Unsaved changes";
}
function download(name: string, data: unknown) {
  const url = URL.createObjectURL(
    new Blob([typeof data === "string" ? data : JSON.stringify(data, null, 2)], { type: typeof data === "string" ? "text/plain" : "application/json" }),
  );
  const a = el("a");
  a.href = url;
  a.download = name;
  a.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function save() {
  if (!draft) return;
  const compatibility = await api("assisted-compatibility", "POST", draft.data);
  if (dirty && !compatibility.compatible) {
    const paths = compatibility.differences.map((d:J)=>d.path).join("\n");
    if (!window.confirm("Save advanced changes?\n\n" + compatibility.message + "\n" + paths + "\n\nCopilot cannot apply conflicting changes. Cancel returns to your unsaved edits."))
      throw new Error("Save cancelled. Your unsaved edits remain in the editor.");
  }
  if (draft.data.characterization?.guided_input) {
    draft.data.characterization.advanced_modified = !compatibility.compatible;
    if (compatibility.compatible) draft.data.characterization.guided_input = compatibility.assisted_copy.characterization.guided_input;
  }
  draft = await api("drafts/" + draft.id, "PATCH", draft.data, draft.version);
  dirty = false;
  notice("Draft saved");
}
async function navigate(next: string) {
  if (dirty) await save();
  tab = next;
  render();
}
function heading(
  title: string,
  description: string,
  actions: HTMLElement[] = [],
) {
  const h = el("div", "heading"),
    left = el("div");
  left.append(
    el("div", "eyebrow", "Anubis / Workload intelligence"),
    el("h1", "", title),
    el("p", "muted", description),
  );
  const a = el("div", "actions");
  a.append(...actions);
  h.append(left, a);
  return h;
}
function render() {
  app.replaceChildren();
  const shell = el("div", "shell"),
    side = el("aside", "sidebar"),
    brand = el("div", "brand");
  const mark=el("img","brandmark") as HTMLImageElement; mark.src="/anubis-logo.png";mark.alt="Anubis weighing a workload against a feather";brand.append(mark, document.createTextNode("ANUBIS"));
  side.append(brand, el("div", "sidecaption", "AI FACTORY WORKLOAD SIZING"));
  const nav = el("nav");
  nav.setAttribute("aria-label", "Main navigation");
  for (const [key, label] of [
    ["cases", "Cases"],
    ["guided", "Discover workload"],
    ["workload", "Workload builder"],
    ["analysis", "Analysis"],
    ["compare", "Compare"],
    ["handoff", "Design handoff"],
    ["deliverables", "Saved deliverables"],
    ["reports", "Reports"],
    ["knowledge", "Knowledge"],
    ["copilot", "Consultant Copilot"],
    ["connections", "AI connections"],
  ]) {
    const b = button(label, () => navigate(key));
    b.classList.toggle("active", tab === key);
    nav.append(b);
  }
  const guide=el("a","","User guide");guide.href="/user-guide.html";guide.target="_blank";guide.rel="noopener";nav.append(guide);
  side.append(
    nav,
    el("div", "sidefoot", "LOCAL ENGINE · v0.1\nDeterministic by design"),
  );
  const work = el("div", "workspace"),
    top = el("header", "topbar");
  top.append(
    el(
      "span",
      "breadcrumb",
      currentCase ? currentCase.data.name : "Workspace / Customer engagements",
    ),
  );
  const status = el("div", "statline"),
    s = el(
      "span",
      "muted",
      dirty
        ? "Unsaved changes"
        : draft
          ? "Saved · revision " + draft.version
          : "Local workspace",
    );
  s.id = "savestate";
  status.append(
    s,
    badge("Planning workspace"),
    button("Sign out", async () => {
      await api("logout", "POST", {});
      login();
    }),
  );
  top.append(status);
  const main = el("main");
  main.id = "main";
  work.append(top, main);
  shell.append(side, work);
  app.append(shell);
  if (["cases", "workload", "analysis", "handoff"].includes(tab)) renderJourney(main);
  if (tab === "guided") void mountGuided(main,api,async(w)=>{await create(w);await run();}).catch(e=>notice(e.message));
  else if (tab === "copilot") void mountCopilot(main,api,{caseId:currentCase?.id,draftId:draft?.id,resultId:result?.id},async(d,cid,review)=>{guidedEntryStep=review?3:0;currentCase=await api("cases/"+cid);draft=d as RecordEntity;result=null;dirty=false;advancedEditor=false;tab="workload";render();},()=>{tab="handoff";render();},()=>{tab="deliverables";render();},()=>{currentCase=null;draft=null;result=null;tab="copilot";render();},async(cid)=>{currentCase=await api("cases/"+cid);tab="closure";render();}).catch(e=>notice(e.message));
  else if (tab === "connections") void mountConnections(main,api).catch(e=>notice(e.message));
  else if (tab === "discovery") void mountDiscovery(main,api,create).catch(e=>notice(e.message));
  else if (tab === "cases") void renderCases(main).catch(e=>notice(e.message));
  else if (tab === "deliverables") void renderDeliverables(main).catch(e=>notice(e.message));
  else if (tab === "closure") void renderClosure(main).catch(e=>notice(e.message));
  else if (tab === "knowledge") void renderKnowledge(main);
  else if (tab === "workload") renderBuilder(main);
  else if (tab === "analysis") renderAnalysis(main);
  else if (tab === "handoff") renderHandoff(main);
  else if (tab === "reports") renderReports(main);
  else if (tab === "compare") void renderCompare(main);
  for (const control of main.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')) {
    const label = control.closest("label");
    if (!label) continue;
    const name = label.textContent?.trim() || "";
    if (!lookupHelp(name)) continue;
    const wrap=el("div","checkbox-guidance"); label.replaceWith(wrap); wrap.append(label);
    fieldGuidance(wrap,name,control);
  }
}
async function renderCases(main: HTMLElement) {
  cases=await api("cases");if(!main.isConnected)return;
  main.append(
    heading(
      "From workload to requirements",
      "Build a defensible workload model. Explore what is known, what is assumed and what needs evidence.",
      [
        button(
          "New engagement",
          async () => {
            tab = "guided"; render();
          },
          true,
        ),
      ],
    ),
  );
  const banner = el(
    "div",
    "warning",
    "Start a new engagement for your customer, or explore an example application below.",
  );
  main.append(banner);
  const scope=panel("MVP 1.0 — supported planning scope");
  scope.append(el("p","",mvpScope));main.append(scope);
  const grid = el("div", "grid");
  const descriptions = [
    "Private maintenance assistant with overnight reports. Separate employee activity, retrieval and batch windows.",
    "Commercial inference service. Model normal traffic, simultaneous bursts and priority reservations.",
    "Continued pretraining campaign. Resolve completion rate, ingestion and checkpoint requirements.",
  ];
  stories.slice(0, 3).forEach((s, i) => {
    const p = panel(s.name);
    p.classList.add("story");
    p.prepend(el("div", "number", "0" + (i + 1) + " / CUSTOMER STORY"));
    p.append(
      el("p", "muted", descriptions[i]),
      button("Build planning example →", () => create(stories[i+4]), true),
      button("Open original incomplete story", () => create(s)),
    );
    grid.append(p);
  });
  main.append(grid);
  const imported = panel("Import a structured workload");
  const file = el("input");
  file.type = "file";
  file.accept = ".json";
  file.setAttribute("aria-label", "Workload JSON");
  file.onchange = async () => {
    try {
      if (file.files?.[0]) await create(JSON.parse(await file.files[0].text()));
    } catch (e) {
      notice((e as Error).message);
    }
  };
  imported.append(
    el(
      "p",
      "muted",
      "Versioned workload JSON is validated by the API. Narrative text remains source context.",
    ),
    file,
  );
  main.append(imported);
  const existing = panel("Your engagements");
  if (!cases.length)
    existing.append(
      el(
        "p",
        "muted",
        "No saved engagements yet. Start with a story or create a new case.",
      ),
    );
  const caseRows: HTMLElement[][] = [];
  for (const c of cases) {
    const actions = el("div", "engagement-actions");
    actions.append(
      button("View engagement", async () => {
        currentCase = c;
        const ds = await api("cases/" + c.id + "/drafts");
        draft = ds[0] || null;
        const rs = await api("cases/" + c.id + "/runs");
        result = rs[0] || null;
        tab = c.data.status === "completed" ? "deliverables" : "workload";
        advancedEditor=false;
        phase = 0;
        dirty = false;
        render();
      }),
    );
    actions.append(button("Delete engagement",async()=>{
      if(!window.confirm(`Move "${c.data.name}" to Trash? It will disappear from Your engagements. Saved calculations and completed versions are retained and can be restored.`))return;
      await api("cases/"+c.id+"/delete","POST",{confirm:true},c.version);
      sessionStorage.removeItem("anubis-copilot-"+c.id);
      if(currentCase?.id===c.id){currentCase=null;draft=null;result=null;dirty=false;}
      render();
    }));
    caseRows.push([
      el("span", "", c.data.name),
      el("span", "engagement-phase", c.workflow?.label || "Active"),
      el("span", "", c.workflow?.next_action || "Review engagement"),
      actions,
    ]);
  }
  if(caseRows.length){
    const grid=table(["Engagement", "Current status", "Next action", "Controls"],caseRows);
    grid.classList.add("engagement-table");
    grid.setAttribute("tabindex","0");grid.setAttribute("role","region");grid.setAttribute("aria-label","Engagement status table");
    grid.querySelector("table")!.setAttribute("aria-label","Engagement status");
    grid.querySelectorAll("th").forEach(th=>th.setAttribute("scope","col"));
    grid.querySelectorAll("tbody tr").forEach(row=>row.classList.add("engagement-row"));
    existing.append(grid);
  }
  main.append(existing);
  const trash=panel("Trash");
  trash.append(el("p","note","Deleted engagements are recoverable. Their records remain stored until restored. This is not permanent erasure."),button("Show deleted engagements",async()=>{
    const deleted=await api("cases/trash");
    const list=el("div");
    for(const c of deleted){const row=el("div","sectionline engagement-row");row.append(el("span","",c.data.name),button("Restore engagement",async()=>{await api("cases/"+c.id+"/restore","POST",{confirm:true},c.version);render();}));list.append(row);}
    if(!deleted.length)list.append(el("p","","Trash is empty."));trash.append(list);
  }));main.append(trash);
}
async function create(workload: J) {
  advancedEditor=false;
  currentCase = await api("cases", "POST", { name: workload.name });
  draft = await api(
    "cases/" + currentCase!.id + "/drafts",
    "POST",
    structuredClone(workload),
  );
  cases = await api("cases");
  result = null;
  dirty = false;
  phase = 0;
  selectedStage = 0;
  tab = "workload";
  render();
}
function renderBuilder(main: HTMLElement) {
  if(draft?.data.characterization?.guided_input && !draft.data.characterization.advanced_modified && !advancedEditor) { const entryStep=guidedEntryStep;guidedEntryStep=0;void mountGuided(main,api,async(w)=>{draft!.data=w;mark();await save();await run();},draft.data.characterization.guided_input,()=>{advancedEditor=true;render();},entryStep).catch(e=>notice(e.message));return; }
  if (!draft) {
    main.append(
      heading("Workload builder", "Choose a customer engagement to begin."),
    );
    return;
  }
  main.append(
    heading(
      draft.data.name,
      "Structured intake · Every engineering quantity has a unit, source and acceptance state.",
      [
        button("Save draft", async () => {
          await save();
          render();
        }),
        button("Validate", async () => {
          await save();
          const v = await api("drafts/" + draft!.id + "/validate", "POST", {});
          notice(
            v.diagnostics.length
              ? JSON.stringify(v.diagnostics)
              : "Valid structure. Evidence readiness is assessed during compilation.",
          );
        }),
        button("Freeze and compile", run, true),
      ],
    ),
  );
  const assisted = panel("Editing options");
  assisted.append(el("p", "", "Viewing this editor does not change your workload. You can calculate here with Freeze and compile. Saved detailed changes are protected from conflicting Copilot updates."), button("Review assisted editing options", async () => {
    const review = await api("assisted-compatibility", "POST", draft!.data);
    assisted.replaceChildren(el("h2", "", "Assisted editing compatibility"), el("p", "", review.message));
    if (review.compatible) assisted.append(button("Return to assisted editing", () => { draft!.data.characterization.guided_input=review.assisted_copy.characterization.guided_input;draft!.data.characterization.advanced_modified=false;advancedEditor=false;render(); }));
    else if (review.can_copy) {
      assisted.append(el("p", "warning", "A separate assisted copy retains the saved application description but replaces the following advanced differences. Your original workload remains unchanged."), el("pre", "", JSON.stringify(review.conversion_preview,null,2)), button("Create separate assisted copy", async () => { if(dirty)await save();const copy=structuredClone(review.assisted_copy);copy.name += " — assisted copy";copy.characterization.guided_input.name=copy.name;await create(copy); }));
    }
  }));
  main.append(assisted);
  if(draft.data.characterization) { const p=panel("Architecture discovery saved"); p.append(el("p","","This description identifies activities and open questions. Refine quantitative inputs before sizing."),button("Review saved discovery",()=>{main.replaceChildren();void mountDiscovery(main,api,create,draft!.data.characterization);})); main.append(p); }
  const steps = el("nav", "steps");
  steps.setAttribute("aria-label", "Workload phases");
  phases.forEach((p, i) => {
    const b = button(`${i + 1} ${p}`, () => {
      phase = i;
      render();
    });
    b.classList.toggle("active", phase === i);
    b.title = phaseGuidance[i];
    if (phase === i) b.setAttribute("aria-current", "step");
    steps.append(b);
  });
  main.append(steps, el("p", "phase-context", `You are here: intake phase ${phase + 1} of 8 — ${phases[phase]}. ${phaseGuidance[phase]}`));
  if (phase === 2) {renderPlanningControls(main); if(draft.data.planning) { const nav=el("div","actions"); nav.append(button("← Previous",()=>{phase--;render();}),button("Continue →",()=>{phase++;render();},true)); main.append(nav); return;}}
  if (phase === 0) {
    const p = panel("Define the engagement");
    p.append(
      input("Workload name", draft.data.name, (v) => {
        draft!.data.name = v;
        mark();
      }),
      select(
        "Factory tenancy",
        draft.data.tenancy,
        ["single", "multi"],
        (v) => {
          draft!.data.tenancy = v;
          mark();
        },
      ),
      area("Customer context and source notes", draft.data.notes || "", (v) => {
        draft!.data.notes = v;
        mark();
      }),
      el(
        "p",
        "note",
        "Notes remain source material. They do not change sizing until represented by structured inputs.",
      ),
    );
    main.append(p);
  } else if (phase === 6) {
    renderScenarios(main);
  } else if (phase === 7) {
    const p = panel("Review the effective workload");
    p.append(
      el(
        "p",
        "muted",
        "Unknowns are allowed. Inactive inputs are excluded when frozen. A completed calculation does not imply an evidence-qualified architecture.",
      ),
      button("Export editable workload", () =>
        download("anubis-workload.json", draft!.data),
      ),
    );
    p.append(
      button("Review agent proposals", async () => {
        if (dirty) await save();
        const proposals: RecordEntity[] = await api(
          "cases/" + currentCase!.id + "/proposals",
        );
        const section = panel("Proposed observations — human review");
        for (const proposal of proposals) {
          if (proposal.data.draft_id !== draft!.id) continue;
          const selected = new Set<number>();
          let rationale = "";
          section.append(
            el(
              "p",
              "note",
              "Author: " +
                proposal.data.author +
                " · Draft version: " +
                proposal.data.draft_version,
            ),
          );
          proposal.data.rows.forEach((row: J, index: number) => {
            const label = el("label", "checkline"),
              check = el("input");
            check.type = "checkbox";
            check.onchange = () => {
              if (check.checked) selected.add(index);
              else selected.delete(index);
            };
            label.append(
              check,
              document.createTextNode(row.stage_id + " / " + row.field),
            );
            section.append(
              label,
              el("pre", "", JSON.stringify(row.observation, null, 2)),
            );
          });
          section.append(
            input("Review rationale", "", (value) => (rationale = value)),
            button("Apply explicitly selected assumptions", async () => {
              const response = await api("proposal-reviews", "POST", {
                proposal_id: proposal.id,
                accept_rows: [...selected],
                rationale,
              });
              draft = response.draft;
              dirty = false;
              notice("Reviewed assumptions applied. provenance retained");
              render();
            }),
          );
        }
        if (!proposals.length)
          section.append(el("p", "muted", "No proposals have been submitted."));
        main.append(section);
      }),
    );
    const flow = el("div", "flow");
    draft.data.stages.forEach((s: J) =>
      flow.append(el("span", "", s.name + " · " + s.type)),
    );
    p.append(flow);
    p.append(
      el(
        "p",
        "note",
        chosenActivation
          ? "Selected knowledge activation: " + chosenActivation
          : draft.data.planning ? "Analytical planning enabled. Compilation estimates GPU and resource requirements from accepted assumptions. measured service qualification remains separate." : "No performance evidence selected. Demand-only compilation.",
      ),
    );
    const importer = el("input");
    importer.type = "file";
    importer.accept = ".json";
    importer.setAttribute("aria-label", "Observation rows JSON");
    importer.onchange = async () => {
      try {
        if (!importer.files?.[0]) return;
        await save();
        const preview = await api("import-previews", "POST", {
          draft_id: draft!.id,
          rows: JSON.parse(await importer.files[0].text()),
        });
        const review = panel("Review observation import");
        review.append(
          el(
            "pre",
            "",
            JSON.stringify(
              {
                accepted: preview.data.accepted,
                rejected: preview.data.rejected,
              },
              null,
              2,
            ),
          ),
          button(
            "Commit reviewed accepted rows",
            async () => {
              draft = await api("import-commits", "POST", {
                preview_id: preview.id,
                accept_partial: true,
              });
              dirty = false;
              render();
            },
            true,
          ),
        );
        main.append(review);
      } catch (e) {
        notice((e as Error).message);
      }
    };
    p.append(el("h3", "", "Import typed observations"), importer);
    const code = el("pre", "", JSON.stringify(draft.data, null, 2));
    p.append(code);
    main.append(p);
  } else {
    const layout = el("div", "editor"),
      list = el("aside", "stage-nav");
    draft.data.stages.forEach((s: J, i: number) => {
      const b = button(s.name || s.id, () => {
        selectedStage = i;
        render();
      });
      b.classList.toggle("selected", i === selectedStage);
      list.append(b);
    });
    list.append(
      button("+ Add stage", () => {
        draft!.data.stages.push({
          id: "stage_" + crypto.randomUUID().slice(0, 8),
          name: "New stage",
          type: "inference",
          observations: {},
        });
        selectedStage = draft!.data.stages.length - 1;
        mark();
        render();
      }),
    );
    layout.append(list);
    const body = panel(phases[phase]);
    const s = draft.data.stages[selectedStage];
    if (!s)
      body.append(el("p", "muted", "Add a stage to describe the application."));
    else {
      if (phase === 1) {
        body.append(
          input("Stage name", s.name, (v) => {
            s.name = v;
            mark();
          }),
          select("Stage type", s.type, types, (v) => {
            s.type = v;
            mark();
            render();
          }),
          area("Stage notes", s.notes || "", (v) => {
            s.notes = v;
            mark();
          }),
          button("Remove stage", () => {
            const removed = s.id;
            draft!.data.stages.splice(selectedStage, 1);
            draft!.data.edges = draft!.data.edges.filter(
              (e: J) => e.from !== removed && e.to !== removed,
            );
            for (const sc of draft!.data.scenarios)
              if (sc.active_stages)
                sc.active_stages = sc.active_stages.filter(
                  (x: string) => x !== removed,
                );
            selectedStage = 0;
            mark();
            render();
          }),
        );
      }
      if (phase === 1) {
        const graph = panel("Stage dependencies");
        graph.append(
          el(
            "p",
            "note",
            "Edges describe execution order. Demand is declared for each stage. no unqualified graph expansion is inferred.",
          ),
        );
        for (const other of draft.data.stages.filter((x: J) => x.id !== s.id)) {
          const label = el("label", "checkline"),
            check = el("input");
          check.type = "checkbox";
          check.checked = (draft.data.edges || []).some(
            (e: J) => e.from === other.id && e.to === s.id,
          );
          check.onchange = () => {
            draft!.data.edges = (draft!.data.edges || []).filter(
              (e: J) => !(e.from === other.id && e.to === s.id),
            );
            if (check.checked)
              draft!.data.edges.push({ from: other.id, to: s.id });
            mark();
          };
          label.append(
            check,
            document.createTextNode("Runs after " + other.name),
          );
          graph.append(label);
        }
        body.append(graph);
      }
      if (phase === 2) {
        const profiles = activeProfiles.filter(
          (p) => p.kind === (s.type === "training" ? "training" : "inference"),
        );
        if (profiles.length)
          body.append(
            select(
              "Available execution evidence",
              "Choose evidence",
              ["Choose evidence", ...profiles.map((p) => p.id)],
              (id) => {
                const p = profiles.find((p) => p.id === id);
                if (!p) return;
                s.fingerprint = structuredClone(p.fingerprint);
                s.model = p.fingerprint.model || "unresolved";
                s.runtime = p.fingerprint.runtime || "unresolved";
                s.precision = p.fingerprint.precision || "unresolved";
                s.platforms = [p.platform];
                mark();
                render();
              },
            ),
          );
        else
          body.append(
            el(
              "p",
              "note",
              "Choose an evidence activation in Knowledge to populate execution options. Customer demand remains independent of the selected benchmark.",
            ),
          );
        if (s.fingerprint)
          body.append(el("pre", "", JSON.stringify(s.fingerprint, null, 2)));
        body.append(
          input(
            "Model revision or unresolved shortlist",
            s.model || "unresolved",
            (v) => {
              s.model = v;
              mark();
            },
          ),
          input("Runtime restriction", s.runtime || "unresolved", (v) => {
            s.runtime = v;
            mark();
          }),
          select(
            "Precision",
            s.precision || "unresolved",
            ["unresolved", "bf16", "fp16", "fp8", "int8", "int4"],
            (v) => {
              s.precision = v;
              mark();
            },
          ),
          el(
            "p",
            "note",
            "Performance evidence must match the exact model, runtime, precision, request shape and service boundaries. A catalogue name alone does not qualify capacity.",
          ),
        );
      }
      if (phase === 3 || phase === 5) {
        body.append(
          el(
            "p",
            "muted",
            phase === 3
              ? "Enter the known activity, work volume and completion windows. Leave material unknowns explicit."
              : "Describe data, retention, IO and movement as separate stages. Object and file tiers remain separate.",
          ),
        );
        const available =
          phaseFields[phase === 3 ? "Demand" : "Data"]?.[s.type] ||
          fields[s.type] ||
          {};
        for (const [name, unit] of Object.entries(available)) {
          if (!s.observations[name]) {
            const b = button("Add " + name.replaceAll("_", " "), () => {
              s.observations[name] = {
                state: "unknown",
                reason: "Not yet supplied",
              };
              mark();
              render();
            });
            body.append(b);
          } else body.append(observation(s, name, unit as string));
        }
        if (phase === 5)
          body.append(
            select(
              "Storage tier",
              s.storage_tier || "object",
              ["object", "file", "local"],
              (v) => {
                s.storage_tier = v;
                mark();
              },
            ),
          );
      }
      if (phase === 4) {
        body.append(
          el(
            "div",
            "warning",
            "Latency qualification requires a precise measurement boundary and applicable serving evidence. Mean token rates cannot establish p95 latency.",
          ),
        );
        for (const slo of s.service_objectives || []) {
          const row = el("div", "row");
          row.append(
            select(
              "Latency metric",
              slo.metric,
              ["ttft", "inter_token_latency", "completion"],
              (v) => {
                slo.metric = v;
                mark();
              },
            ),
            input("Percentile", slo.percentile, (v) => {
              slo.percentile = v;
              mark();
            }),
            input("Target", slo.target.value, (v) => {
              slo.target.value = v;
              mark();
            }),
            select("Time unit", slo.target.unit, ["ms", "s"], (v) => {
              slo.target.unit = v;
              mark();
            }),
          );
          body.append(
            row,
            input("Measurement boundary", slo.boundary, (v) => {
              slo.boundary = v;
              mark();
            }),
          );
        }
        body.append(
          button("+ Add service objective", () => {
            s.service_objectives = s.service_objectives || [];
            s.service_objectives.push({
              metric: "ttft",
              percentile: "95",
              target: {
                state: "estimated",
                value: "1",
                unit: "s",
                origin: "customer",
                source: "consultant interview",
              },
              boundary: "Define client or model-service boundary",
            });
            mark();
            render();
          }),
        );
      }
    }
    layout.append(body);
    main.append(layout);
  }
  const nav = el("div", "actions");
  if (phase > 0)
    nav.append(
      button("← Previous", () => {
        phase--;
        render();
      }),
    );
  if (phase < 7)
    nav.append(
      button(
        "Continue →",
        () => {
          phase++;
          render();
        },
        true,
      ),
    );
  main.append(nav);
}
function observation(s: J, name: string, defaultUnit: string) {
  const q = s.observations[name],
    p = el("div", "obs");
  const active = el("label", "checkline"),
    toggle = el("input");
  toggle.type = "checkbox";
  toggle.checked = q.active !== false;
  toggle.onchange = () => {
    q.active = toggle.checked;
    mark();
  };
  active.append(toggle, document.createTextNode("Include in frozen workload"));
  p.append(active);
  const intro=el("div","quantity-help"); intro.append(el("h3","",name.replaceAll("_"," "))); fieldGuidance(intro,name,undefined,quantityHelp[name]); p.append(intro);
  p.append(
    select(
      name.replaceAll("_", " ") + " · state",
      q.state,
      ["unknown", "known", "estimated", "assumed"],
      (v) => {
        q.state = v;
        if (v === "unknown") {
          delete q.value;
          delete q.unit;
        } else {
          q.value = q.value || "";
          q.unit = q.unit || defaultUnit;
          q.origin = q.origin || "customer";
          q.source = q.source || "consultant interview";
        }
        mark();
        render();
      },
    ),
  );
  if (q.state === "unknown") {
    p.append(
      input("Reason", q.reason || "", (v) => {
        q.reason = v;
        mark();
      }),
    );
    return p;
  }
  p.append(
    input("Value", q.value || "", (v) => {
      q.value = v;
      mark();
    }),
    select("Unit", q.unit, units, (v) => {
      q.unit = v;
      mark();
    }),
    select(
      "Origin",
      q.origin || "customer",
      ["customer", "measurement", "template", "agent"],
      (v) => {
        q.origin = v;
        mark();
      },
    ),
  );
  const source = input("Source reference", q.source || "", (v) => {
    q.source = v;
    mark();
  });
  source.classList.add("source");
  p.append(source);
  if (q.state === "assumed") {
    const l = el("label"),
      x = el("input");
    x.type = "checkbox";
    x.checked = !!q.accepted;
    x.onchange = () => {
      q.accepted = x.checked;
      mark();
    };
    l.append(x, document.createTextNode("Accept this explicit assumption"));
    p.append(l);
  }
  const l = el("label"),
    x = el("input");
  x.type = "checkbox";
  x.checked = q.active !== false;
  x.onchange = () => {
    q.active = x.checked;
    mark();
  };
  l.append(x, document.createTextNode("Active in effective input"));
  p.append(l);
  return p;
}
function renderScenarios(main: HTMLElement) {
  for (const s of draft!.data.scenarios) {
    const p = panel(s.name || s.id),
      row = el("div", "row");
    row.append(
      input("Scenario name", s.name || s.id, (v) => {
        s.name = v;
        mark();
      }),
      input("Demand multiplier", s.multiplier || "1", (v) => {
        s.multiplier = v;
        mark();
      }),
      input(
        "Unavailable nodes",
        String(s.failed_nodes || 0),
        (v) => {
          s.failed_nodes = Number(v);
          mark();
        },
        "number",
      ),
    );
    p.append(
      row,
      el(
        "p",
        "note",
        "Only selected stages run simultaneously in this scenario. Empty selection means no stages.",
      ),
    );
    for (const stage of draft!.data.stages) {
      const l = el("label"),
        x = el("input");
      x.type = "checkbox";
      x.checked = !s.active_stages || s.active_stages.includes(stage.id);
      x.onchange = () => {
        if (!s.active_stages)
          s.active_stages = draft!.data.stages.map((t: J) => t.id);
        s.active_stages = x.checked
          ? [...new Set([...s.active_stages, stage.id])]
          : s.active_stages.filter((id: string) => id !== stage.id);
        mark();
      };
      l.append(x, document.createTextNode(stage.name));
      p.append(l);
    }
    main.append(p);
  }
  main.append(
    button("+ Add scenario", () => {
      draft!.data.scenarios.push({
        id: "scenario_" + crypto.randomUUID().slice(0, 8),
        name: "New scenario",
        multiplier: "1",
        failed_nodes: 0,
      });
      mark();
      render();
    }),
  );
}
async function run() {
  await save();
  const revision = await api(
    "drafts/" + draft!.id + "/freeze",
    "POST",
    {},
    draft!.version,
  );
  const acts: RecordEntity[] = await api("activations");
  const active = acts.find(
    (x) => x.id === chosenActivation && !x.data.withdrawn,
  );
  const job = await api("compilations", "POST", {
    revision_id: revision.id,
    ...(active ? { activation_id: active.id } : {}),
  });
  notice("Compilation queued · " + job.id);
  const thisRun = ++runToken;
  for (let i = 0; i < 120; i++) {
    await new Promise((r) => setTimeout(r, 250));
    const j = await api("jobs/" + job.id);
    if (thisRun !== runToken) return;
    if (j.data.state === "succeeded") {
      result = await api("results/" + j.data.result_id);
      tab = "analysis";
      document.querySelector<HTMLElement>("#notice")!.style.display = "none";
      render();
      return;
    }
    if (j.data.state === "failed" || j.data.state === "cancelled")
      throw new Error(j.data.error?.message || j.data.state);
  }
  notice(
    "Job continues in the service. Reload the engagement to retrieve its result.",
  );
}
function table(headers: string[], rows: HTMLElement[][]) {
  const wrap = el("div", "table-wrap"),
    t = el("table"),
    thead = el("thead"),
    tr = el("tr");
  headers.forEach((h) => {
    const th = el("th", "", h);
    th.scope = "col";
    tr.append(th);
  });
  thead.append(tr);
  const body = el("tbody");
  for (const row of rows) {
    const tr = el("tr");
    for (const e of row) {
      const td = el("td");
      td.append(e);
      tr.append(td);
    }
    body.append(tr);
  }
  t.append(thead, body);
  wrap.append(t);
  return wrap;
}
function renderPlanningControls(main: HTMLElement) {
  if(!draft) return;
  const box=panel("Planning assumptions and architecture");
  if(!draft.data.planning) {
    box.append(button("Enable analytical planning",()=>{
      draft!.data.planning=structuredClone(stories[4].planning);
      draft!.data.planning.assumptions_accepted=false;
      for(const st of draft!.data.stages) if(["inference","batch","training"].includes(st.type)) {
        st.planning=structuredClone(stories[4].stages[0].planning);
        if(st.type==="training") {st.planning.model="dense30b";st.planning.parallel_gpus=8;}
      }
      mark();render();
    })); main.append(box);return;
  }
  const p=draft.data.planning;
  box.append(el("p","note","Analytical planning with editable assumptions. These are not measured performance or guaranteed latency."),select("Architecture profile",p.architecture,planningCatalog.architectures.map((a:J)=>a.id),(v)=>{p.architecture=v;mark();}));
  for(const [k,label] of Object.entries({sensitivity_percent:"Throughput sensitivity percent",compute_efficiency:"Compute efficiency fraction",memory_efficiency:"Memory bandwidth efficiency fraction",minimum_service_fraction:"Minimum accepted service fraction",bytes_per_token:"External bytes per token",protocol_allowance:"Protocol allowance multiplier",expansion_lead_days:"Expansion lead days"})) box.append(input(label,String(p[k]),(v)=>{p[k]=k==="expansion_lead_days"?Number(v):v;mark();}));
  for(const [k,label] of [["assumptions_accepted","Accept these planning assumptions"],["accept_capacity_shortfall","Accept reduced service at a lower anchor"]]) {
    const l=el("label"),c=el("input");c.type="checkbox";c.checked=!!p[k];c.onchange=()=>{p[k]=c.checked;mark();};l.append(c,document.createTextNode(label));box.append(l);
  }
  for(const st of draft.data.stages) if(st.planning) {
    const a=st.planning;box.append(el("h3","",st.name||st.id),select("Planning model — "+st.id,a.model,Object.keys(planningCatalog.models),(v)=>{a.model=v;mark();}));
    for(const [k,v] of Object.entries(a))if(k!=="model" && !(st.type!=="training" && ["activation_GB_per_gpu","training_bytes_per_parameter"].includes(k)))box.append(input(st.id+" · "+k,String(v),(value)=>{a[k]=typeof v==="number"?Number(value):value;mark();}));
  }
  main.append(box);
}
function renderPlanningResult(main:HTMLElement,p:J) {
  const overview=panel("Your requirements at a glance");
  overview.append(el("p","note","Planning estimates with explicit assumptions. Measurement required means unresolved, not zero."),table(["Requirement","Calculated value","What this means"],requirementsRows(p).map(row=>row.map(v=>el("span","",v)))),button("Download requirements summary",()=>download("anubis-requirements-summary.txt",requirementsText(p))));
  main.append(overview);
  if(p.networks){const n=p.networks,wan=n.external_customer_datacenter,storage=n.storage,ew=n.east_west;
    const value=(x:any)=>x==null?'Needs measurement':`${x} Gbps`;
    const box=panel('Four network requirements');box.append(table(['Network role','Sizing requirement','Meaning'],[
      ['External customer datacenter connection',value(wan.required_ingress_lower_bound_Gbps),`Initial load: ${value(wan.initial_load_link_Gbps)}. Ongoing ingress: ${value(wan.steady_ingress_lower_bound_Gbps)}. Egress: ${value(wan.steady_egress_lower_bound_Gbps)}. RTT target: ${wan.round_trip_target_ms??'Unspecified'} ms.`],
      ['North-south factory traffic',`${value(n.north_south.ingress_lower_bound_Gbps)} in / ${value(n.north_south.egress_lower_bound_Gbps)} out`,n.north_south.scope],
      ['Dedicated storage network',`${value(storage.read_link_lower_bound_Gbps)} read / ${value(storage.write_link_lower_bound_Gbps)} write`,'Physically separate Ethernet fabric. No converged network. Size both directions and confirm initial-load writes and checkpoint bursts.'],
      ['East-west GPU network',`${ew.fabric}. ${value(ew.per_gpu_link_lower_bound_Gbps)} per GPU`,ew.scope]
    ].map(row=>row.map(x=>el('span','',x)))));box.append(el('p','note',n.basis),el('p','note',`Usable link fraction: ${n.usable_link_fraction}. Protocol allowance: ${n.protocol_allowance}. These are lower-bound planning rates, not selected circuit or switch port speeds.`));for(const note of n.follow_up)box.append(el('p','scope-notice',note));main.append(box);
  }

  if(!p.stage_calculations.length && p.status==="unknown") {
    const box=panel("Sizing measurements required");
    box.append(el("p","scope-notice","GPU count, GPU memory and host provisions are not estimated for this workload. No factory deployment is recommended yet."));
    for(const gap of p.gaps)box.append(el("p","",gap));
    if(p.storage.length)box.append(table(["Storage tier","Usable bytes","Read B/s","Write B/s"],p.storage.map((t:J)=>[t.tier,t.usable_bytes,t.read_Bps??"Unspecified",t.write_Bps??"Unspecified"].map(x=>el("span","",String(x))))));
    box.append(button("Download planning architecture brief",()=>download("anubis-planning-brief.json",p)));main.append(box);return;
  }
  if(p.hardware_comparison) {
    const comparison=panel("GPU workload comparison");
    comparison.append(el("p","note","Same workload and assumptions on each GPU. Counts include whole 8-GPU nodes and declared failure reserves. These are workload estimates. deployment anchors and downstream design tool platform support are separate."));
    comparison.append(table(["GPU", "Estimated GPUs", "Sensitivity range", "VRAM required / available", "Status"],p.hardware_comparison.map((h:J)=>[h.platform,h.stage_calculations.length?String(h.raw_gpus):"Not estimated",h.stage_calculations.length?`${h.upside_gpus}–${h.downside_gpus}`:"—",`${h.required_GB_per_gpu} / ${h.provided_GB_per_gpu} GB`,h.status].map((x:string)=>el("span","",x)))));
    comparison.append(button("Download GPU comparison",()=>download("anubis-gpu-comparison.json",p.hardware_comparison))); main.append(comparison);
  }
  const box=panel("GPU deployment recommendation");
  box.append(badge(p.status),el("p","",`Initial deployment: ${p.initial_gpus ?? "unresolved"} GPUs · ${p.nodes_or_trays ?? "—"} nodes/trays · ${p.architecture.platform} · ${p.architecture.fabric}`),el("p","note",`${p.status==="unknown"?"Supported-component GPU subtotal":"Raw workload requirement"}: ${p.raw_gpus} GPUs. Sensitivity: ${p.upside_gpus}–${p.downside_gpus}. GPU shortfall: ${p.shortfall_gpus ?? 0}.`));
  if (p.workload_capacity) {
    const capacity = p.workload_capacity;
    for (const [label, value] of [["Minimum supported architecture", capacity.minimum_architecture], ["Selected deployment", capacity.selected_architecture]] as const) {
      if (!value) continue;
      const fit = value.supports_one_instance_compute === null ? "unresolved" : value.supports_one_instance_compute ? "yes, conditionally" : "no";
      box.append(el("p", "", `${label} (${value.gpus} GPUs): supports one complete workload instance in compute terms: ${fit}. Equivalent workload instances: ${value.equivalent_instances_compute ?? "unresolved"}. sensitivity range: ${value.downside_instances_compute ?? "—"}–${value.upside_instances_compute ?? "—"}.`));
    }
    box.append(el("p", "note", capacity.basis), el("p", "note", capacity.qualification));
  }

  box.append(table(["Resource","Planning requirement"],[
    ["VRAM required / provided per GPU",`${p.required_GB_per_gpu} / ${p.provided_GB_per_gpu} GB`],
    ["Host RAM required / provided",`${p.host_ram_GB_required} / ${p.host_ram_GB_provided ?? "Not selected"} GB`],
    ["Local disk / CPU provision",`${p.local_disk_GB_required} GB / ${p.cpu_cores_provision} cores`],
    ["Declared traffic ingress / egress before link-utilization allowance",`${p.ingress_Gbps} / ${p.egress_Gbps} Gbps`],
    ["Tenancy",p.tenancy], ["Next expansion anchor",p.expansion_anchor?String(p.expansion_anchor.gpus)+" GPUs":"Beyond supported profile"],
  ].map(row=>row.map(x=>el("span","",String(x))))));
  box.append(table(["Storage tier","Usable bytes","Read B/s","Write B/s"],p.storage.map((t:J)=>[t.tier,t.usable_bytes,t.read_Bps ?? "Not specified",t.write_Bps ?? "Not specified"].map(x=>el("span","",String(x))))));
  box.append(el("p","note",p.network_scope),el("p","note",p.storage_network_policy),el("p","note",p.expansion_trigger));
  for(const gap of p.gaps)box.append(el("p","warning",gap));
  for(const note of p.limitations)box.append(el("p","note",note));
  const detail=el("details");detail.append(el("summary","","Assumptions and calculations"),el("pre","",JSON.stringify({policy:p.policy,calculations:p.stage_calculations},null,2)));box.append(button("Download planning architecture brief",()=>download("anubis-planning-brief.json",p)),detail);main.append(box);
}
function renderAnalysis(main: HTMLElement) {
  if (result) {
    const next=panel("Next step: Design handoff");
    next.classList.add("copilot-next-step");
    next.append(el("p", "", "Your calculation is complete. Review the GPU estimates and open requirements below, then continue to stage 4 using this saved result. You do not need to return to Consultant Copilot."),button("Continue to Design handoff",()=>{tab="handoff";render();window.scrollTo(0,0);},true),el("p", "note", "On the next screen, review the target configuration and select Prepare projection. This produces the executive summary, design intake and companion requirements. It does not submit a design run."));
    main.append(next);
  }
  if(result?.data.result.guided_context) renderGuidedContext(main);
  main.append(
    heading(
      "Workload analysis",
      "Immutable results · All quantities are returned by the deterministic compiler.",
      result
        ? [
            button("Export result", () =>
              download("anubis-result.json", result!.data.result),
            ),
            button(
              "Create report",
              async () => {
                await api("reports", "POST", { result_id: result!.id });
                tab = "reports";
                render();
              },
              true,
            ),
          ]
        : [],
    ),
  );
  if (!result) {
    main.append(
      el(
        "div",
        "panel empty",
        "Compile a workload to inspect its requirements.",
      ),
    );
    return;
  }
  const r = result.data.result;
  if(r.planning) renderPlanningResult(main,r.planning);
  if (r.characterization)
    main.append(
      el(
        "p",
        "note",
        r.characterization.workload_character.replaceAll("_", " ") +
          " · " +
          r.characterization.basis,
      ),
    );
  const metrics = el("div", "metrics");
  for (const [title, value, foot] of [
    ["Derived facts", String(r.facts.length), "Units and scope attached"],
    ["Candidates", String(r.candidates.length), "Per stage and scenario"],
    [
      "Open questions",
      String(r.questions.length),
      "Clarifications and evidence",
    ],
    ["Evidence", r.knowledge_channel, "Qualification stays explicit"],
  ]) {
    const m = el("div", "metric");
    m.append(
      el("span", "", title),
      el("strong", "", value),
      el("span", "", foot),
    );
    metrics.append(m);
  }
  main.append(metrics, el("div", "warning", r.scope));
  const p = panel("Derived workload requirements");
  p.append(
    table(
      ["Stage / scenario", "Requirement", "Value", "Evidence", "Trace"],
      r.facts.map((f: J) => [
        el("span", "", f.stage_id + " / " + f.scenario_id),
        el("span", "", f.name.replaceAll("_", " ")),
        el("strong", "", f.display || f.value + " " + f.unit),
        badge(f.evidence_basis),
        button("Inspect", () => {
          const old = document.querySelector("#inspector");
          old?.remove();
          const x = el("section", "panel inspector");
          x.id = "inspector";
          x.append(
            el("h2", "", f.name.replaceAll("_", " ")),
            el(
              "pre",
              "",
              JSON.stringify(
                r.derivations.find((d: J) => d.id === f.derivation_id),
                null,
                2,
              ),
            ),
          );
          main.append(x);
          x.scrollIntoView({ behavior: "smooth" });
        }),
      ]),
    ),
  );
  main.append(p);
  const portfolio = panel("Factory compute reservation envelopes");
  for (const x of r.factory_configurations || []) {
    portfolio.append(
      el(
        "h3",
        "",
        x.platform + " · " + x.gpus + " GPUs / " + x.nodes + " nodes",
      ),
      badge(x.status),
      el("p", "note", x.policy),
      el("p", "muted", x.scope),
    );
  }
  if (!(r.factory_configurations || []).length)
    portfolio.append(
      el("p", "muted", "No evidence-supported reservation envelope yet."),
    );
  main.append(portfolio);
  const c = panel("Execution alternatives");
  if (!r.candidates.length)
    c.append(
      el(
        "p",
        "muted",
        "GPU count is unresolved. Add qualified model, runtime, memory and service evidence to assess configurations.",
      ),
    );
  else
    c.append(
      table(
        ["Platform", "Scope", "GPUs / nodes", "Feasibility", "Action"],
        r.candidates.map((x: J) => [
          el("span", "", x.platform),
          el("span", "", x.stage_id + " / " + x.scenario_id),
          el("strong", "", x.gpus + " / " + x.nodes),
          badge(x.status),
          button("Review constraints", () => {
            const d = panel("Candidate constraints");
            d.append(el("pre", "", JSON.stringify(x, null, 2)));
            main.append(d);
            d.scrollIntoView();
          }),
        ]),
      ),
    );
  main.append(c);
  const infrastructure = panel("Storage and connectivity configurations");
  if (!(r.resource_candidates || []).length)
    infrastructure.append(
      el(
        "p",
        "muted",
        "No product-specific evidence selected. Capacity and transfer requirements remain visible above.",
      ),
    );
  for (const candidate of r.resource_candidates || []) {
    infrastructure.append(
      el(
        "h3",
        "",
        candidate.vendor +
          " / " +
          candidate.product +
          " / " +
          candidate.configuration,
      ),
      badge(candidate.status),
      el("p", "note", candidate.scope),
      button("Inspect resource constraints", () => {
        infrastructure.append(
          el("pre", "", JSON.stringify(candidate, null, 2)),
        );
      }),
    );
  }
  main.append(infrastructure);
  const q = panel("Clarifications that matter");
  if (!r.questions.length)
    q.append(
      el(
        "p",
        "muted",
        "No additional input questions from the currently supported evaluators. Domain qualifications still apply.",
      ),
    );
  for (const x of r.questions)
    q.append(el("p", "", x.stage_id + " — " + x.message));
  q.append(
    el("small", "", `Run ${result.id} · Semantic digest ${r.semantic_digest}`),
  );
  main.append(q);
}
function renderHandoff(main: HTMLElement) {
  const canProject=Boolean(result?.data.result.candidates?.length);
  main.append(heading("Design handoff",canProject?"Keep intended hardware separate from the platform used to model the architecture.":"Review the current limitations and choose how to conclude this engagement."));
  const next=panel(canProject?"Stage 4: prepare your design inputs":"Stage 4: conclude or continue discovery");
  next.append(el("p","",canProject
    ?"This handoff uses your saved calculation. Review the configuration below, then select Prepare projection to generate the executive summary and downloadable design inputs. Unresolved requirements remain visible in the companion specification."
    :"No resolved design candidate is available for a projection. You do not need to invent a GPU count or return to an earlier stage to close this engagement. You can document the current findings and limitations in a final status report, or continue gathering evidence."));
  if(currentCase)next.append(button("Review final status report",()=>{tab="closure";render();window.scrollTo(0,0);},!canProject));
  if(!canProject&&currentCase)next.append(button("Continue gathering workload evidence",()=>{tab="copilot";render();window.scrollTo(0,0);}));
  if(result)next.append(button("Back to calculation results",()=>{tab="analysis";render();window.scrollTo(0,0);}));
  main.append(next);
  if(!canProject||!result)return;
  const coverage=panel('Where each network requirement goes');
  coverage.append(el('p','note','Prepare projection creates a partial intake plus a readable brief and companion specification. Sending the intake alone does not transfer every network requirement.'),table(['Network','Downstream intake','Brief and companion specification'],[
    ['East-west GPU fabric','Selected fabric family','Per-GPU bandwidth, assumptions and unresolved measurements'],
    ['Dedicated storage fabric','Ethernet technology only','Physical separation, no convergence, read/write bandwidth and validation requirements'],
    ['North-south traffic','No verified matching field','Ingress and egress requirements for the factory boundary'],
    ['External customer datacenter connection','No verified matching field','Initial-load volume/window, derived link rates, ongoing transfers and round-trip latency target']
  ].map(row=>row.map(value=>el('span','',value)))),el('p','scope-notice','Download all three outputs. The architect must apply brief-only requirements in the downstream tool or design process. Ethernet alone does not enforce a dedicated storage network.'));main.append(coverage);

  if(result?.data.result.guided_context) renderGuidedContext(main);
  const p = panel("Prepare an existing-field intake");
  let candidate = result.data.result.candidates[0].id,
    platform = result.data.result.planning?.architecture.platform || "HGX_B300",
    fabric = result.data.result.planning?.architecture.fabric || "InfiniBand",
    accepted = false,
    projectName = draft?.data.name || currentCase!.data.name;
  p.append(
    input("Design project name", projectName, (v) => (projectName = v)),
    select(
      "Intended candidate",
      candidate,
      result.data.result.candidates.map((x: J) => x.id),
      (v) => (candidate = v),
    ),
    select(
      "Design modelling platform",
      platform,
      ["HGX_B300", "GB300_NVL72"],
      (v) => (platform = v),
    ),
    select(
      "Modelling fabric choice",
      fabric,
      ["InfiniBand", "Spectrum-X"],
      (v) => (fabric = v),
    ),
    el(
      "p",
      "note",
      "This is an architect-selected modelling option, not a claim that the engine has established this fabric as necessary.",
    ),
  );
  const l = el("label"),
    check = el("input");
  check.type = "checkbox";
  check.onchange = () => (accepted = check.checked);
  l.append(
    check,
    document.createTextNode(
      "Accept the explicit modelling substitution and retain physical specifications outside the design tool",
    ),
  );
  p.append(
    l,
    button(
      "Prepare projection",
      async () => {
        const pr = await api("neon-projections", "POST", {
          result_id: result!.id,
          mapping: {
            candidate_id: candidate,
            platform,
            network_fabric: fabric,
            accept_substitution: accepted,
            project_name: projectName,
          },
        });
        const summary = panel("AI Factory design executive summary");
        summary.append(el("p", "note", "What this projection means for your design. Generated from saved calculation and mapping fields using fixed narrative rules."));
        const bullets = el("ul");
        for (const item of projectionSummary(pr.data)) {
          const li = el("li");
          li.append(el("strong", "", item.title + ": "), document.createTextNode(item.text));
          const trace = el("details");
          trace.append(el("summary", "", "Source fields"), el("p", "note", item.sources.join(", ")));
          li.append(trace); bullets.append(li);
        }
        summary.append(bullets, button("Download executive summary", () => download("anubis-executive-summary.txt", projectionSummaryText(pr.data))), el("small", "note", "Narrative rules: " + projectionGrammarVersion));
        main.append(summary);
        const view = panel("Projection and mapping ledger");
        view.append(
          el(
            "div",
            "warning",
            "Planning handoff to the configured local design target. Production qualification is separate. retain companion requirements.",
          ),
          button("Download design intake", () =>
            download("neon-intake.json", pr.data.payload),
          ),
          button("Download readable architecture brief", () => download("anubis-architecture-brief.txt", pr.data.worksheet)),
          button("Download companion specification", () =>
            download("anubis-neon-companion.json", pr.data),
          ),
          button("Submit experimental local design run", async () => {
            const caps = await api("integration-capabilities");
            if (!caps.submission_enabled)
              throw new Error(
                "No reviewed local target configured. use manual exchange.",
              );
            const job = await api("neon-submissions", "POST", {
              projection_id: pr.id,
              confirm_experimental_submission: true,
            });
            notice("Design run submitted: " + job.id);
            for (let i = 0; i < 180; i++) {
              await new Promise((r) => setTimeout(r, 500));
              const state = await api("jobs/" + job.id);
              if (state.data.assessment_id) {
                const assessment = await api(
                  "assessments/" + state.data.assessment_id,
                );
                view.prepend(el("p","success", "Design tool returned architecture · requested " + assessment.data.field_reconciliation?.[0]?.requested + " GPUs / returned " + assessment.data.field_reconciliation?.[0]?.returned + " GPUs"));
                view.append(
                  el(
                    "pre",
                    "",
                    JSON.stringify(
                      {
                        field_reconciliation:
                          assessment.data.field_reconciliation,
                        domains: assessment.data.domains,
                        external_authority: assessment.data.external_authority,
                      },
                      null,
                      2,
                    ),
                  ),
                  button("Export returned design assessment", () =>
                    download("neon-assessment.json", assessment.data),
                  ),
                );
                return;
              }
              if (
                ["failed", "outcome_unknown", "cancelled"].includes(
                  state.data.state,
                )
              )
                throw new Error(
                  state.data.state + ": " + JSON.stringify(state.data.error),
                );
            }
            notice("Design job continues. inspect job " + job.id);
          }),
          el("pre", "", JSON.stringify(pr.data, null, 2)),
        );
        main.append(view);
        appendCompletion(main,pr);
      },
      true,
    ),
  );
  main.append(p);
  main.append(button("View saved projections and completed versions",()=>{tab="deliverables";render();}));
}
function appendCompletion(host:HTMLElement,pr:J) {
 const box=panel("Complete this engagement");
 box.append(el("p","","Completion records requirements delivery. It does not approve the downstream architecture or qualify performance. Your selected calculation and projection will be preserved for future retrieval."),el("p","note",`Selected calculation: ${pr.data.result_id}. Selected projection: ${pr.id}.`));
 const notes=el("textarea");notes.setAttribute("aria-label","Completion notes");notes.maxLength=4000;
 const label=el("label","","Consultant notes (optional)");label.append(notes);box.append(label);
 const confirm=el("input");confirm.type="checkbox";const cl=el("label","","I confirm that these selected requirements are delivered.");cl.prepend(confirm);box.append(cl);
 const earlier=el("input");earlier.type="checkbox";const sl=el("label","","If newer edits exist, I explicitly intend to deliver this earlier saved calculation.");sl.prepend(earlier);box.append(sl);
 box.append(button("Complete engagement",async()=>{
  if(!confirm.checked)throw Error("Confirm the selected requirements are delivered before completing.");
  const c=await api("cases/"+pr.case_id);
  const saved=await api("cases/"+pr.case_id+"/complete","POST",{result_id:pr.data.result_id,projection_id:pr.id,notes:notes.value,confirm_delivery:true,acknowledge_stale:earlier.checked,executive_summary:projectionSummaryText(pr.data),narrative_version:projectionGrammarVersion},c.version);
  currentCase=saved.case;tab="deliverables";render();window.scrollTo(0,0);
 },true));host.append(box);
}
function appendSavedDownloads(host:HTMLElement,projection:J,calculation:J,summary:string) {
 host.append(button("Download executive summary",()=>download("anubis-executive-summary.txt",summary)),button("Download design intake",()=>download("anubis-design-intake.json",projection.payload)),button("Download architecture brief",()=>download("anubis-architecture-brief.txt",projection.worksheet)),button("Download companion specification",()=>download("anubis-companion.json",projection)),button("Download calculation result",()=>download("anubis-result.json",calculation)));
}
async function renderDeliverables(main:HTMLElement) {
 main.append(heading("Saved deliverables","Retrieve exact saved handoffs and completed engagement versions."));
 if(!currentCase){main.append(el("p","","Open an engagement from Cases to retrieve its deliverables."));return;}
 const cid=currentCase.id;
 const [c,completions,projections]=await Promise.all([api("cases/"+cid),api("cases/"+cid+"/completions"),api("cases/"+cid+"/saved-projections")]);
 if(!main.isConnected)return;currentCase=c;
 const status=panel(c.data.name);status.append(el("p","",c.data.status==="completed"?(c.data.completion_outcome==="concluded_without_handoff"?"Closed — final status report issued. No design handoff delivered.":"Completed — requirements delivered. Saved versions remain available after reopening."):"Active engagement. Earlier completed versions remain unchanged."));
 if(c.data.status==="completed")status.append(button("Reopen engagement for revisions",async()=>{currentCase=await api("cases/"+cid+"/reopen","POST",{notes:"Reopened from saved deliverables"},c.version);const ds=await api("cases/"+cid+"/drafts");draft=ds[0]||null;dirty=false;advancedEditor=false;
  sessionStorage.removeItem("anubis-copilot-"+cid);
  if(currentCase!.data.copilot_resume_session_id)sessionStorage.setItem("anubis-copilot-"+cid,currentCase!.data.copilot_resume_session_id);
  tab="copilot";render();},true));
 if(c.data.status!=="completed")status.append(button("Continue with Copilot",async()=>{
   const ds=await api("cases/"+cid+"/drafts");draft=ds[0]||null;
   sessionStorage.removeItem("anubis-copilot-"+cid);
   if(draft){const compatibility=await api("assisted-compatibility","POST",draft.data);
     if(compatibility.can_copy){const ctx=await api("copilot-context/"+cid);const previous=ctx.sessions[0]?.data;
       const session=await api("copilot-sessions","POST",{case_id:cid,draft_id:draft.id,classification:previous?.classification||"corporate",profile_id:previous?.profile_id||""});
       sessionStorage.setItem("anubis-copilot-"+cid,session.id);
     }
   }
   currentCase=c;dirty=false;advancedEditor=false;tab="copilot";render();
 },true));
 if(c.data.status!=="completed")status.append(button("Conclude with a final status report",()=>{tab="closure";render();}));
 main.append(status);
 for(const completion of completions){
  const d=completion.data,box=panel("Completed version · "+new Date(d.completed_at*1000).toLocaleString());
  if(d.outcome==="concluded_without_handoff"){
    box.append(el("p","",d.meaning),el("p","",`Closed by ${d.completed_by}. ${d.notes}`),el("pre","",d.report_text),button("Download final status report",()=>download("anubis-final-status-report.txt",d.report_text)),button("Download complete closure record",()=>download("anubis-closure-record.json",completion)));
    main.append(box);continue;
  }
  box.append(el("p","",d.meaning),el("p","",`Completed by ${d.completed_by}. ${d.notes||"No consultant notes."}`),el("p","note",`Calculation ${d.result_id} · Projection ${d.projection_id}`));
  if(d.earlier_calculation_acknowledged)box.append(el("p","warning","The consultant explicitly selected an earlier calculation despite newer workload edits."));
  const summary=el("details");summary.append(el("summary","","Read saved executive summary"),el("pre","",d.executive_summary||"No narrative was recorded for this completed version."));box.append(summary);
  appendSavedDownloads(box,d.projection_snapshot,d.result_snapshot,d.executive_summary||"");
  box.append(button("Download complete engagement record",()=>download("anubis-completed-engagement.json",completion)),button("View this calculation",async()=>{result=await api("results/"+d.result_id);tab="analysis";render();}));main.append(box);
 }
 if(!completions.length)main.append(el("p","","No completed version yet. Select a saved projection below or prepare one in Design handoff."));
 const history=panel("Saved projection history");
 for(const pr of projections){const row=panel("Projection "+pr.id);row.append(el("p","note",`Calculation: ${pr.data.result_id}`));row.append(button("Open saved projection",async()=>{
  const r=await api("results/"+pr.data.result_id);result=r;
  const detail=panel("Saved projection deliverables");detail.append(el("pre","",projectionSummaryText(pr.data)));appendSavedDownloads(detail,pr.data,r.data,projectionSummaryText(pr.data));main.append(detail);
  if(c.data.status!=="completed")appendCompletion(main,pr);
  detail.scrollIntoView({behavior:"smooth"});
 }));history.append(row);}
 if(!projections.length)history.append(el("p","","No projections saved yet. Calculate requirements, then prepare a projection in Design handoff."));main.append(history);
}
async function renderClosure(main:HTMLElement) {
 main.append(heading("Conclude with a final status report","Close the engagement with its findings and limitations, without claiming a design handoff."));
 if(!currentCase){main.append(el("p","","Open an engagement first."));return;}
 const cid=currentCase.id;
 const [c,review]=await Promise.all([api("cases/"+cid),api("cases/"+cid+"/closure-review")]);if(!main.isConnected)return;
 if(c.data.status==="completed"){main.append(el("p","","This engagement is already closed. Its saved record remains available."),button("View saved deliverables",()=>{tab="deliverables";render();}));return;}
 const assessment=panel("Current findings and limitations");assessment.append(el("p","scope-notice",review.reason),el("p","note","Assessment basis: "+review.basis),el("p","","Anubis identifies current limitations, not permanent impossibility. You may continue discovery, obtain specialist evidence, or conclude now with this status report."));main.append(assessment);
 const report=panel("Final status report preview");report.append(el("pre","",review.report_text));main.append(report);
 const form=panel("Confirm conclusion");const notes=el("textarea");notes.setAttribute("aria-label","Reason for concluding now");notes.maxLength=4000;const label=el("label","","Reason for concluding now and recommended next action");label.append(notes);
 const confirm=el("input");confirm.type="checkbox";const cl=el("label","","I confirm closure with a status report, without delivering a design handoff.");cl.prepend(confirm);
 const close=button("Close with final status report",async()=>{
   if(!confirm.checked||!notes.value.trim())throw Error("Record the reason and confirm closure without a handoff.");
   const saved=await api("cases/"+cid+"/close-with-report","POST",{review_digest:review.review_digest,notes:notes.value.trim(),confirm:true},c.version);
   currentCase=saved.case;tab="deliverables";render();window.scrollTo(0,0);
 },true);close.disabled=review.running_jobs;
 form.append(label,cl,close,button("Continue working on this engagement",()=>{tab="copilot";render();}));
 if(review.running_jobs)form.append(el("p","warning","A job is still active. Let it finish or cancel it, then refresh this review before closing."));
 form.append(button("Refresh status report preview",()=>render()));main.append(form);
}
function renderReports(main: HTMLElement) {
  main.append(
    heading(
      "Customer requirements report",
      "A presentation of the same immutable compiler facts.",
      [button("Print / save PDF", () => window.print())],
    ),
  );
  if (!result) {
    main.append(el("div", "panel empty", "Compile a workload first."));
    return;
  }
  const r = result.data.result,
    p = panel(currentCase?.data.name || "Workload requirements");
  p.append(
    el("p", "", r.scope),
    el(
      "div",
      "warning",
      "Demonstration evidence only. Business acceptance, selection and engineering verification are separate states.",
    ),
    el(
      "p",
      "",
      `Engine ${r.engine_version} · Revision ${result.data.revision_id}`,
    ),
    table(
      ["Requirement", "Scope", "Value"],
      r.facts.map((f: J) => [
        el("span", "", f.name.replaceAll("_", " ")),
        el("span", "", f.stage_id + " / " + f.scenario_id),
        el("strong", "", f.display || f.value + " " + f.unit),
      ]),
    ),
    button("Export exact dossier", () =>
      download("anubis-dossier.json", result!.data),
    ),
  );
  main.append(p);
}
async function renderCompare(main: HTMLElement) {
  main.append(
    heading(
      "Compare immutable runs",
      "Separate workload changes from knowledge changes before attributing an effect.",
    ),
  );
  if (!currentCase) return;
  try {
    const comparisonCases: RecordEntity[] = await api("cases");
    const runs: RecordEntity[] = (await Promise.all(comparisonCases.map(async c => (await api("cases/"+c.id+"/runs")).map((r:RecordEntity)=>({...r,data:{...r.data,case_name:c.data.name}}))))).flat();
    if (runs.length < 2) {
      main.append(
        el(
          "div",
          "panel empty",
          "Compile at least two revisions or scenario variants to compare.",
        ),
      );
      return;
    }
    let left = runs[1].id,
      right = runs[0].id;
    const p = panel("Comparison baselines");
    p.append(
      select(
        "Earlier run",
        left,
        runs.map((x) => x.id),
        (v) => (left = v),
      ),
      select(
        "Later run",
        right,
        runs.map((x) => x.id),
        (v) => (right = v),
      ),
      button(
        "Compare",
        async () => {
          const d = await api("comparisons", "POST", {
            left_id: left,
            right_id: right,
          });
          p.append(el("pre", "", JSON.stringify(d, null, 2)));
        },
        true,
      ),
    );
    for(const option of p.querySelectorAll("option")){const run=runs.find(r=>r.id===option.value);if(run)option.textContent=run.data.case_name+" · "+run.id;}
    main.append(p);
  } catch (e) {
    notice((e as Error).message);
  }
}
async function renderKnowledge(main: HTMLElement) {
  main.append(
    heading(
      "Knowledge registry",
      "Immutable evidence packages, explicit activation and independent production qualification.",
    ),
  );
  const p = panel("Import an evidence package"),
    file = el("input");
  file.type = "file";
  file.accept = ".json";
  file.setAttribute("aria-label", "Evidence package JSON");
  file.onchange = async () => {
    try {
      if (file.files?.[0]) {
        const data = JSON.parse(await file.files[0].text());
        await api("packs", "POST", data);
        notice("Immutable package imported");
        render();
      }
    } catch (e) {
      notice((e as Error).message);
    }
  };
  p.append(
    el(
      "p",
      "muted",
      "Import knowledge/synthetic.json to exercise the placement oracle. Synthetic evidence cannot activate for production.",
    ),
    file,
  );
  main.append(p);
  try {
    const packs: RecordEntity[] = await api("packs");
    for (const pack of packs) {
      const q = panel(pack.data.pack.id + " · " + pack.data.pack.version);
      q.append(
        badge(pack.data.pack.channel),
        el("p", "muted", pack.data.pack.description || ""),
        el("code", "", pack.data.digest),
        button("Activate for demonstration", async () => {
          const activation = await api(
            "packs/" + pack.id + "/activate",
            "POST",
            { channel: "demonstration" },
          );
          useActivation(activation);
          notice("Demonstration activation selected for subsequent runs");
        }),
      );
      main.append(q);
    }
    const acts: RecordEntity[] = await api("activations");
    if (acts.length) {
      const q = panel("Activation history");
      for (const a of acts) {
        const row = el("div", "sectionline");
        row.append(
          el(
            "p",
            "",
            a.data.pack_id +
              " · " +
              (a.data.withdrawn ? "withdrawn" : a.data.channel),
          ),
        );
        if (!a.data.withdrawn)
          row.append(
            button("Use for next compilation", () => {
              useActivation(a);
              notice("Knowledge lock selected");
            }),
            button("Withdraw activation", async () => {
              await api("activations/" + a.id + "/withdraw", "POST", {});
              render();
            }),
          );
        q.append(row);
      }
      main.append(q);
    }
  } catch (e) {
    notice((e as Error).message);
  }
}
function login() {
  app.replaceChildren();
  const p = el("main", "panel login");
  p.id = "main";
  p.append(
    el("div", "brand", "ANUBIS"),
    el("h1", "", "Workload Sizing Engine"),
    el(
      "p",
      "muted",
      "Sign in to your local deterministic engineering workspace.",
    ),
  );
  p.append(el("p","note","First login: open the project’s .anubis/identities.json file. Find your user entry and copy only the token value, without quotation marks. Paste it below. On this computer the project is /Users/trai/Code/anubis. For a shared deployment, request your own token from the administrator."));
  let token = "";
  const f = el("form");
  f.append(input("Access token", "", (v) => (token = v), "password"));
  const b = el("button", "primary", "Open workspace");
  b.type = "submit";
  f.append(b);
  f.onsubmit = async (e) => {
    e.preventDefault();
    try {
      const r = await fetch("/api/v1/session", {
        method: "POST",
        headers: {
          Authorization: "Bearer " + token,
          "Content-Type": "application/json",
        },
        body: "{}",
      });
      if (!r.ok) throw new Error("Authentication failed");
      token = "";
      await start();
    } catch (e) {
      notice((e as Error).message);
    }
  };
  p.append(
    f,
    el(
      "p",
      "note",
      "Your token is exchanged for an HttpOnly local session. It is not stored in browser local storage.",
    ),
  );
  app.append(p);
}
async function start() {
  try {
    await api("me");
    [cases, stories] = await Promise.all([api("cases"), api("stories")]);
    planningCatalog = await api("planning-catalog");
    const descriptors = await api("component-descriptors");
    fields = descriptors.fields;
    phaseFields = descriptors.phase_fields;
    render();
  } catch (e) {
    login();
    if (!(e as Error).message.startsWith("unauthorized:"))
      notice((e as Error).message);
  }
}
window.addEventListener("beforeunload", (e) => {
  if (dirty) {
    e.preventDefault();
    e.returnValue = "";
  }
});
void start();

function renderGuidedContext(main:HTMLElement){
 const context=result!.data.result.guided_context;const c=context.characterization;architectureView(main,c.components.map((component:J,i:number)=>({...component,...(c.guided_input?.components?.[i]||{})})));
 const p=panel("Requirements and next measurements");
 for(const q of c.follow_up)p.append(el("p","scope-notice",q));
 p.append(el("p","","Entered quantities are estimates. retained presets are assumptions. Blank storage capacity is unspecified. Host resources are provisions. Network rates cover declared application traffic. bulk transfers and latency require separate inputs."));
 const plan=result?.data.result.planning;
 if(plan){p.append(el("p","",plan.status==="unknown"?"Partial estimate: GPU subtotals exclude unresolved components. No complete deployment recommendation is available.":"Workload GPU demand and infrastructure deployment anchors are separate decisions."));
 p.append(table(["Application component","Demand","GPU subtotal","Sizing driver"],plan.stage_calculations.map((x:J)=>[c.components.find((v:J)=>v.id===x.stage_id)?.name||x.stage_id,x.demand+' '+x.capacity_unit,String(x.raw_gpus),x.rule].map((v:string)=>el("span","",v)))));}
 p.append(button("Download requirements brief",()=>{const lines=[context.name,"Application requirements",...c.components.map((v:J)=>`${v.name}: ${v.pattern}. ${v.location}. ${v.support}`),"Follow-up measurements",...c.follow_up,"Results and assumptions",JSON.stringify(plan||result?.data.result||{},null,2),"Customer notes",context.notes||""];const blob=new Blob([lines.join("\n\n")],{type:"text/plain"});const a=el("a");a.href=URL.createObjectURL(blob);a.download="anubis-requirements-brief.txt";a.click();URL.revokeObjectURL(a.href);}));main.append(p);
}
