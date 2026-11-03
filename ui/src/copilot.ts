import {readinessPanel} from './readiness.js';
import { factReview, manualFactForm, demandForm } from "./fact-review.js";
import { architectureView } from "./guided.js";
type J = Record<string, any>;
type API = (
  path: string,
  method?: string,
  body?: unknown,
  version?: number,
) => Promise<any>;
const labels: Record<string, string> = {
  components: "Application components",
  rate: "Peak requests per minute",
  calls: "Model calls per request",
  input_tokens: "Input tokens per call",
  output_tokens: "Output tokens per call",
  retrieval: "Search location",
  location: "Compute location",
  model: "Model preset",
  pattern: "Application pattern",
  name: "Name",
  network: "Network measurements",
  overlap: "Operating overlap",
  tenancy: "Factory users",
  storage_tb: "Retained storage in TB",
};
const label = (key: string) => labels[key] || key.replaceAll("_", " ");
const display = (value: any): string =>
  Array.isArray(value)
    ? value.map((v) => display(v)).join("\n\n")
    : value && typeof value === "object"
      ? Object.entries(value)
          .map(([k, v]) => label(k) + ": " + (v === "" ? "Not specified" : v))
          .join("\n")
      : String(value);
const el = (tag: string, text = "", cls = "") => {
  const e = document.createElement(tag);
  e.textContent = text;
  e.className = cls;
  return e;
};
function input(label: string, value = "", area = false) {
  const wrap = el("label", label, "field");
  const x = document.createElement(area ? "textarea" : "input");
  x.value = value;
  x.setAttribute("aria-label", label);
  wrap.append(x);
  return { wrap, x };
}
export async function mountCopilot(
  host: HTMLElement,
  api: API,
  context: { caseId?: string; draftId?: string; resultId?: string },
  open: (draft: J, caseId: string, review?: boolean) => Promise<void>,
  handoff: () => void,
  showDeliverables?: () => void,
  newEngagement?: () => void,
  reviewClosure?: (caseId:string) => void,
) {
  const [caps, profiles, me, activations] = await Promise.all([
    api("copilot-capabilities"),
    api("copilot-profiles"),
    api("me"),
    api("activations"),
  ]);
  if (!host.isConnected) return;
  if(context.caseId){
    const engagement=await api("cases/"+context.caseId);
    if(engagement.data.status==="completed"){
      host.replaceChildren(el("h1","Completed engagement — historical record"),el("h2",engagement.data.name),el("p","This engagement is complete. Its saved workload remains available for reference, but no Copilot work is in progress. View its deliverables or reopen it explicitly before making revisions.","scope-notice"));
      const view=el("button","View saved deliverables or reopen") as HTMLButtonElement;
      view.onclick=()=>showDeliverables?.();host.append(view);
      const fresh=el("button","Start a new assisted engagement") as HTMLButtonElement;
      fresh.onclick=()=>{if(newEngagement)newEngagement();else void mountCopilot(host,api,{},open,handoff,showDeliverables);};host.append(fresh);
      return;
    }
  }
  let session: J | null = null,
    error = "",
    busy = false,
    history: J = { sources: [], proposals: [], jobs: [] },
    jobId = "",
    facts: J | null = null;
  let closure:J|null=null;
  let startedAt=0, jobState="queued";
  function updateProgress(){
    const elapsed=Math.max(0,Math.floor((Date.now()-startedAt)/1000));
    const text=jobState==="queued"?"Queued — waiting for the model service":jobState==="cancel_requested"?"Cancellation requested — waiting for confirmation":"Working — interpreting your description and validating proposed facts";
    host.querySelectorAll<HTMLElement>("[data-copilot-progress]").forEach(node=>{node.textContent=text;});
    host.querySelectorAll<HTMLElement>("[data-copilot-elapsed]").forEach(node=>{node.textContent=`Elapsed: ${elapsed} seconds. ${elapsed>=30?"This is taking longer than usual. The request is still being checked. You may cancel or wait.":"Duration depends on the model service. Your accepted workload is unchanged."}`;});
  }
  const remembered = context.caseId
    ? sessionStorage.getItem("anubis-copilot-" + context.caseId)
    : null;
  if (remembered)
    try {
      session = await api("copilot-sessions/" + remembered);
    } catch {}
  if (!session && context.caseId) {
    const c = await api("copilot-context/" + context.caseId);
    session = c.sessions.at(0) || null;
  }
  let currentDraft: J | null = context.draftId ? await api("drafts/" + context.draftId) : null;
  let compatibility: J | null = currentDraft ? await api("assisted-compatibility", "POST", currentDraft.data) : null;
  if (context.resultId) facts = await api("copilot-facts/" + context.resultId);
  async function refresh() {
    if (session) {
      session = await api("copilot-sessions/" + session.id);
      history = await api("copilot-sessions/" + session!.id + "/history");
      closure=await api("cases/"+session!.case_id+"/closure-review");
      if (session!.data.draft_id) {
        currentDraft = await api("drafts/" + session!.data.draft_id);
        compatibility = await api("assisted-compatibility", "POST", currentDraft!.data);
      }
      if (context.resultId)
        facts = await api("copilot-facts/" + context.resultId);
    }
    draw();
  }
  function button(label: string, fn: () => void | Promise<void>) {
    const b = el("button", label) as HTMLButtonElement;
    b.type = "button";
    b.onclick = async () => {
      b.disabled = true;
      try {
        error = "";
        await fn();
      } catch (e) {
        error = (e as Error).message;
        draw();
      } finally {
        b.disabled = false;
      }
    };
    return b;
  }
  async function wait(job: J) {
    busy = true;
    jobId = job.id;startedAt=Date.now();jobState=job.data?.state||"queued";
    draw();
    try {
      for (let i = 0; i < 180; i++) {
        if (!host.isConnected) return;
        await new Promise((r) => setTimeout(r, 500));
        const r = await api("jobs/" + job.id);
        jobState=r.data.state;updateProgress();
        if (!["queued", "running", "cancel_requested"].includes(r.data.state)) {
          if (r.data.state !== "succeeded")
            throw Error(r.data.error?.message || "Operation " + r.data.state);
          await refresh();
          return r;
        }
      }
      throw Error("Operation is still running. Refresh to inspect its status.");
    } finally {
      busy = false;
      jobId = "";
      if (host.isConnected) draw();
    }
  }
  async function start(name: string, classification: string) {
    let cid = context.caseId;
    if (!cid) {
      const c = await api("cases", "POST", { name });
      cid = c.id;
      context.caseId = cid;
    }
    session = await api("copilot-sessions", "POST", {
      case_id: cid,
      ...(context.draftId ? { draft_id: context.draftId } : {}),
      classification,
    });
    sessionStorage.setItem("anubis-copilot-" + cid, session!.id);
    await refresh();
  }
  function select(label: string, choices: [string, string][], value = "") {
    const wrap = el("label", label, "field");
    const x = document.createElement("select");
    x.setAttribute("aria-label", label);
    for (const [v, t] of choices) {
      const o = document.createElement("option");
      o.value = v;
      o.textContent = t;
      x.append(o);
    }
    if (value) x.value = value;
    wrap.append(x);
    return { wrap, x };
  }
  function draw() {
    host.replaceChildren();
    host.append(
      el("h1", "Consultant Copilot"),
      el(
        "p",
        "Describe your application, review proposed inputs, then use the deterministic engine to calculate requirements. You can continue in the workload builder at any time.",
      ),
    );
    host.dataset.busy=String(busy);
    if(busy){
      const activity=el("section","","copilot-activity");activity.setAttribute("aria-label","Copilot activity");
      const spinner=el("span","","copilot-spinner");spinner.setAttribute("aria-hidden","true");
      const status=el("strong");status.dataset.copilotProgress="";status.setAttribute("role","status");status.setAttribute("aria-live","polite");
      const elapsed=el("p");elapsed.dataset.copilotElapsed="";
      activity.append(spinner,status,elapsed);host.append(activity);updateProgress();
    }
    const alert = el("p", error, "warning");
    alert.setAttribute("role", "alert");
    if (error) host.append(alert);
    const guide = document.createElement("a");
    guide.href = "/copilot-guide.txt";
    guide.target = "_blank";
    guide.rel = "noopener";
    guide.textContent = "Copilot setup and user guide";
    host.append(guide);
    if (caps.disabled)
      host.append(
        el(
          "p",
          "AI assistance is disabled by the deployment administrator. Manual proposal review and workload editing remain available.",
          "warning",
        ),
      );
    if (currentDraft && compatibility && (!compatibility.compatible || (session && session.data.draft_id === currentDraft.id && session.data.draft_version !== currentDraft.version))) {
      const protection = el("section", "", "panel");
      protection.append(el("h2", "Your saved workload is protected"), el("p", compatibility.message), el("p", "You can continue editing and calculate requirements in the advanced editor. Copilot changes must preserve the detailed settings listed below."));
      if (compatibility.differences.length) {
        const details=el("details");details.append(el("summary", "Detailed settings to preserve"), el("pre", JSON.stringify(compatibility.differences,null,2)));protection.append(details);
      }
      protection.append(button("Continue editing or calculate requirements", async () => {
        const d=structuredClone(currentDraft!); if(d.data.characterization)d.data.characterization.advanced_modified=!compatibility!.compatible;
        await open(d,d.case_id);
      }));
      if (compatibility.can_copy) {
        if (session && session.data.draft_version !== currentDraft.version) protection.append(button("Review latest saved workload with Copilot", async () => {session=null;await start(currentDraft!.data.name,"corporate");}));
        const copy=el("details");copy.append(el("summary", "Review a separate assisted copy"),el("p", "The copy retains the saved assisted description. The differences listed here will be replaced by the assisted version. The original remains unchanged."),el("pre",JSON.stringify(compatibility.conversion_preview,null,2)),button("Create separate assisted copy",async()=>{
          const w=structuredClone(compatibility!.assisted_copy);w.name+=" — assisted copy";w.characterization.guided_input.name=w.name;
          const c=await api("cases","POST",{name:w.name});const d=await api("cases/"+c.id+"/drafts","POST",w);await open(d,c.id);
        }));protection.append(copy);
      }
      host.append(protection);
      if (!compatibility.can_copy) {
        if(facts)host.append(el("h2","Saved calculation results"),el("p","These are the existing deterministic results, not a new calculation."),el("pre",display(facts.planning)));
        host.append(button("Start a separate assisted engagement",()=>{context.caseId=undefined;context.draftId=undefined;session=null;currentDraft=null;compatibility=null;draw();}));
        return;
      }
    }
    if (!session) {
      const name = input("Customer workload name", "New customer engagement"),
        classification = select("Data classification", [
          ["corporate", "Corporate — approved corporate connections only"],
          ["public", "Public — permitted for direct provider processing"],
        ]);
      host.append(
        name.wrap,
        classification.wrap,
        button("Start assisted engagement", () =>
          start(name.x.value, classification.x.value),
        ),
      );
      return;
    }
    if(session.data.reopened_from_completion)host.append(el("p","Engagement reopened. Continue with Copilot using the latest saved workload. Previous conversations and completed deliveries are preserved. Describe the changes you want to make below.","scope-notice"));
    const layout = el("div", "", "copilot-layout"),
      main = el("section", "", "copilot-main"),
      panel = el("aside", "", "copilot-panel");
    panel.setAttribute("aria-label", "Consultant Copilot controls");
    panel.setAttribute("aria-busy",String(busy));
    layout.append(main, panel);
    host.append(layout);
    main.append(
      el("h2", session.data.input.name),
      el(
        "p",
        `Accepted input revision ${session.data.revision}. Data classification: ${session.data.classification}. Model proposals do not change this revision until reviewed.`,
      ),
    );
    const next = el("section", "", "panel copilot-next-step");
    next.id = "copilot-next-step";
    next.setAttribute("tabindex", "-1");
    next.append(el("h2", "Your next step"));
    const steps = el("ol", "", "copilot-progress");
    ["Describe workload", "Review and accept facts", "Review assumptions and calculate", "GPU results and design handoff"].forEach((name, i) => {
      const item = el("li", name);
      const current = session!.data.draft_id ? 2 : history.proposals.length ? 1 : 0;
      if (i === current) item.setAttribute("aria-current", "step");
      steps.append(item);
    });
    next.append(steps);
    if (session.data.draft_id) {
      next.append(el("p", "Your accepted facts are saved. Next, review the planning assumptions and select Calculate estimate. The results screen will show the GPU estimates and comparisons, followed by the design handoff."));
      if (session.data.ready_for_estimate === false)
        next.append(el("p", "Some details still need confirmation. Review the open questions below. You can inspect the estimate assumptions now, but unresolved or specialist work may not produce a complete GPU count.", "scope-notice"));
      next.append(button("Review and calculate GPU estimate", async () => {
        const d = await api("drafts/" + session!.data.draft_id);
        await open(d, session!.case_id, true);
      }));
    } else {
      next.append(el("p", history.proposals.length
        ? "Review the proposed facts below, confirm the assumptions and select Apply selected. Then continue here to calculate your GPU estimate."
        : "Describe your workload using the form. Anubis will propose facts for you to review before calculating an estimate."));
    }
    const gpuCheck=el("section");next.append(gpuCheck);
    const proposed=history.proposals.find((p:J)=>p.data.state==="proposed")?.data.preview;
    void api("guided-readiness","POST",proposed||session.data.input).then(report=>{if(!gpuCheck.isConnected)return;readinessPanel(gpuCheck,report,session!.data.draft_id?async()=>{const d=await api("drafts/"+session!.data.draft_id);await open(d,session!.case_id,true);}:undefined);}).catch(()=>{gpuCheck.textContent="GPU readiness check unavailable. Resolve connection before calculating.";});
    main.append(next);
    if (session.data.input.components.length) {
      architectureView(main, session.data.input.components);
      main.append(
        button("Expand architecture diagram", () => {
          const dialog = document.createElement("dialog");
          dialog.setAttribute(
            "aria-label",
            "Expanded application architecture",
          );
          dialog.className = "architecture-dialog";
          dialog.append(button("Close diagram", () => dialog.remove()));
          architectureView(dialog, session!.data.input.components);
          host.append(dialog);
          dialog.showModal();
        }),
      );
    } else
      main.append(
        el(
          "p",
          "Your application diagram will appear after you review the proposed architecture. Describe who uses the application, what it does, where models run and whether it searches documents or runs scheduled jobs.",
        ),
      );
    const controls = el("div", "", "actions");
    controls.append(button("Refresh session", refresh));
    if (session.data.draft_id)
      controls.append(
        button("Open workload builder and calculate", async () => {
          const d = await api("drafts/" + session!.data.draft_id);
          await open(d, session!.case_id);
        }),
      );
    controls.append(
      button("Fork comparison scenario", async () => {
        const name = window.prompt(
          "Scenario name",
          session!.data.input.name + " alternative",
        );
        if (!name) return;
        session = await api(
          "copilot-sessions/" + session!.id + "/fork",
          "POST",
          { name },
        );
        context.caseId = session!.case_id;
        context.draftId = undefined;
        sessionStorage.setItem(
          "anubis-copilot-" + session!.case_id,
          session!.id,
        );
        await refresh();
      }),
    );
    controls.append(
      button("Start fresh session", async () => {
        session = null;
        await start("Engagement", "corporate");
      }),
    );
    if(reviewClosure)controls.append(button("Conclude with a final status report",()=>reviewClosure(session!.case_id)));
    main.append(controls);
    if(closure?.offer_status_closure&&reviewClosure){
      const limit=el("section","","panel");limit.append(el("h2","A status report can conclude this engagement"),el("p",closure.reason),el("p","You can keep gathering evidence, or review a final status report and close without a design handoff."),button("Review final status report",()=>reviewClosure(session!.case_id)));main.append(limit);
    }
    if (session.data.next_question)
      main.append(el("p", session.data.next_question, "scope-notice"));
    if (caps.fact_definitions)
      main.append(
        manualFactForm(caps, session, async (payload, statement) => {
          try {
            const source = await api(
              "copilot-sessions/" + session!.id + "/sources",
              "POST",
              {
                name: "Consultant fact entry",
                kind: "message",
                text: statement,
              },
            );
            for (const f of payload.facts) {
              f.source_id = source.id;
              f.quote = statement;
            }
            await api(
              "copilot-sessions/" + session!.id + "/proposals",
              "POST",
              payload,
            );
            await refresh();
          } catch (e) {
            error = (e as Error).message;
            draw();
          }
        }),
      );
    main.append(
      demandForm(session, async (payload, statement) => {
        try {
          const source = await api(
            "copilot-sessions/" + session!.id + "/sources",
            "POST",
            {
              name: "Consultant demand measurement",
              kind: "message",
              text: statement,
            },
          );
          for (const f of payload.facts) {
            f.source_id = source.id;
            f.quote = statement;
          }
          await api(
            "copilot-sessions/" + session!.id + "/proposals",
            "POST",
            payload,
          );
          await refresh();
        } catch (e) {
          error = (e as Error).message;
          draw();
        }
      }),
    );
    const library = el("details");
    library.append(el("summary", "Architecture library and measurement guide"));
    for (const c of caps.architecture_library?.cards || []) {
      const card = el("section", "", "panel");
      card.append(
        el("h3", c.name),
        el("p", c.description),
        el("p", "Example: " + c.example),
        el("p", "Distinction: " + c.counterexample),
        el("p", c.caution),
        el("p", "Measure: " + c.measurement_points.join(". ")),
      );
      architectureView(card, [
        {
          name: c.name,
          pattern: c.id,
          location: "unknown",
          retrieval: "unknown",
        },
      ]);
      library.append(card);
    }
    main.append(library);
    for (const proposal of history.proposals) {
      const card = el("section", "", "panel");
      card.append(el("h3", "Input proposal — " + proposal.data.state));
      if (proposal.data.question) card.append(el("p", proposal.data.question));
      if (proposal.data.facts) card.append(factReview(proposal.data));
      const chosen = new Set<number>();
      const table = el("table");
      const header = el("tr");
      for (const t of [
        "Apply",
        "UI field",
        "Proposed value",
        "Basis and source",
      ])
        header.append(el("th", t));
      table.append(header);
      proposal.data.changes.forEach((row: J, i: number) => {
        const tr = el("tr"),
          td = el("td"),
          check = document.createElement("input");
        check.type = "checkbox";
        check.checked = true;
        check.disabled =
          proposal.data.state !== "proposed" || !!proposal.data.facts;
        check.setAttribute("aria-label", "Apply " + row.field);
        chosen.add(i);
        check.onchange = () =>
          check.checked ? chosen.add(i) : chosen.delete(i);
        td.append(check);
        tr.append(td);
        const label = el("td");
        label.append(
          el(
            "strong",
            row.field.startsWith("components.")
              ? "Component " +
                  (Number(row.field.split(".")[1]) + 1) +
                  " " +
                  (labels[row.field.split(".")[2]] || row.field.split(".")[2])
              : labels[row.field] || row.field,
            "copilot-label",
          ),
        );
        const value = el("td");
        value.append(el("code", display(row.value), "copilot-value"));
        const basis = el(
          "td",
          row.basis.replaceAll("_", " ") +
            "\n" +
            row.reason +
            (row.source_id
              ? "\nSource: " + row.source_id + "\n“" + row.quote + "”"
              : ""),
        );
        tr.append(label, value, basis);
        table.append(tr);
      });
      if (proposal.data.facts) {
        const details = el("details");
        details.append(el("summary", "Translated workload inputs"), table);
        card.append(details);
      } else card.append(table);
      if (
        proposal.data.state === "proposed" &&
        proposal.data.base_revision !== session.data.revision
      )
        card.append(
          el(
            "p",
            "This proposal predates the accepted inputs. Ask for a fresh proposal.",
            "warning",
          ),
        );
      if (proposal.data.preview.components.length) {
        const map = el("details");
        map.append(el("summary", "Preview proposed architecture"));
        architectureView(map, proposal.data.preview.components);
        card.append(map);
      }
      if (
        proposal.data.state === "proposed" &&
        proposal.data.changes.length &&
        proposal.data.base_revision === session.data.revision
      ) {
        const accept = el(
          "label",
          "I reviewed the selected values and accept the planning assumptions.",
        );
        const cb = document.createElement("input");
        cb.type = "checkbox";
        accept.prepend(cb);
        card.append(
          accept,
          button("Apply selected", async () => {
            if (!cb.checked)
              throw Error("Review and accept the planning assumptions first.");
            await api("copilot-proposals/" + proposal.id + "/apply", "POST", {
              selected: [...chosen],
              accept_assumptions: true,
            });
            await refresh();
            const next = host.querySelector<HTMLElement>("#copilot-next-step");
            next?.scrollIntoView({ behavior: "smooth", block: "start" });
            next?.focus({ preventScroll: true });
          }),
          button("Discard proposal", async () => {
            await api(
              "copilot-proposals/" + proposal.id + "/reject",
              "POST",
              {},
            );
            await refresh();
          }),
        );
        if (!proposal.data.facts) {
          const simple = el("details");
          simple.append(el("summary", "Edit values using fields"));
          const edits = structuredClone(proposal.data.changes).map(
            ({ field, value, basis, source_id, quote, reason }: J) => ({
              field,
              value,
              basis,
              source_id,
              quote,
              reason,
            }),
          );
          const editField = (row: J, target: J, key: string, title: string) => {
            const value = target[key];
            if (typeof value !== "string" && typeof value !== "boolean") return;
            const f = input(title, String(value));
            if (typeof value === "boolean") {
              f.x.setAttribute("type", "checkbox");
              (f.x as HTMLInputElement).checked = value;
            }
            f.x.oninput = () => {
              target[key] =
                typeof value === "boolean"
                  ? (f.x as HTMLInputElement).checked
                  : f.x.value;
              row.basis = "planning_assumption";
              row.source_id = "";
              row.quote = "";
              row.reason =
                "Consultant edited this value. Retain as a planning assumption until supported by evidence.";
            };
            simple.append(f.wrap);
          };
          for (const row of edits) {
            if (Array.isArray(row.value))
              row.value.forEach((c: J, i: number) => {
                for (const key of Object.keys(c))
                  editField(
                    row,
                    c,
                    key,
                    "Component " + (i + 1) + " " + label(key),
                  );
              });
            else if (row.value && typeof row.value === "object") {
              for (const key of Object.keys(row.value))
                editField(row, row.value, key, label(key));
            } else editField(row, row, "value", label(row.field));
          }
          simple.append(
            el(
              "p",
              "Edited values become explicit planning assumptions. Validate them to create a fresh proposal before applying.",
            ),
            button("Validate edited fields", async () => {
              await api(
                "copilot-sessions/" + session!.id + "/proposals",
                "POST",
                { question: proposal.data.question, changes: edits },
              );
              await refresh();
            }),
          );
          card.append(simple);
          const edit = el("details");
          edit.append(el("summary", "Advanced proposal JSON"));
          const content = input(
            "Editable proposal JSON",
            JSON.stringify(
              {
                question: proposal.data.question,
                changes: proposal.data.changes.map(
                  ({ field, value, basis, source_id, quote, reason }: J) => ({
                    field,
                    value,
                    basis,
                    source_id,
                    quote,
                    reason,
                  }),
                ),
              },
              null,
              2,
            ),
            true,
          );
          edit.append(
            content.wrap,
            button("Validate edited proposal", async () => {
              await api(
                "copilot-sessions/" + session!.id + "/proposals",
                "POST",
                JSON.parse(content.x.value),
              );
              await refresh();
            }),
          );
          card.append(edit);
        }
      }
      main.append(card);
    }
    if (facts) {
      const result = el("section", "", "panel");
      result.append(
        el("h2", "Explain saved results"),
        el(
          "p",
          "Values below come directly from the deterministic engine. Check the workload builder for edits made after this result.",
        ),
      );
      if (
        facts.stale ||
        (session.data.fact_contract &&
          facts.source_draft_id !== session.data.draft_id)
      )
        result.append(
          el(
            "p",
            "These saved results predate current workload edits. Recalculate before using them for design.",
            "warning",
          ),
        );
      const p = facts.planning;
      result.append(
        el(
          "p",
          `Workload GPU count: ${p.raw_gpus ?? "Unresolved"}. Deployment GPU count: ${p.initial_gpus ?? "Unresolved"}. Status: ${p.status ?? "Unknown"}.`,
        ),
      );
      for (const name of [
        "hardware_comparison",
        "stage_calculations",
        "networks",
        "storage",
        "sensitivity",
        "workload_capacity",
      ])
        if (p[name]) {
          const d = el("details");
          d.append(
            el("summary", name.replaceAll("_", " ")),
            el("pre", JSON.stringify(p[name], null, 2)),
          );
          result.append(d);
        }
      result.append(button("Prepare design handoff", handoff));
      main.append(result);
    }
    panel.append(el("p","YOUR WORKSPACE","copilot-panel-eyebrow"),el("h2", "Describe and refine"),el("p","1. Tell us about the workload or answer the next question. 2. Select Ask copilot. 3. Review the proposed facts on the left before applying them.","copilot-panel-guide"));
    const model = select(
      "Model connection",
      profiles
        .filter((p: J) => p.data.provider !== "mcp" || p.data.model_tool)
        .map((p: J) => [p.id, `${p.data.name} — ${p.data.health}`]),
      session.data.profile_id,
    );
    panel.append(model.wrap);
    const knowledge = select("Approved knowledge context", [
      ["", "Architecture and planning catalogue only"],
      ...activations
        .filter((a: J) => !a.data.withdrawn)
        .map(
          (a: J) => [a.id, a.id + " — " + a.data.channel] as [string, string],
        ),
    ]);
    panel.append(
      knowledge.wrap,
      el(
        "p",
        "Selecting a knowledge pack permits its context to be sent to this model connection. Evidence status is preserved.",
      ),
    );
    panel.append(
      el(
        "p",
        "API credentials stay on the backend. A chat subscription is not a model API connection. Changing the connection never changes accepted inputs.",
      ),
    );
    const message = input("What should we know about the workload?", "", true);
    message.x.setAttribute(
      "placeholder",
      "Example: Staff ask questions over manuals. Search already runs in our datacenter. Peak demand is 600 questions per minute.",
    );
    message.x.disabled=busy;
    panel.append(message.wrap);
    const ask = button("Ask copilot", async () => {
      if (busy) return;
      if (!message.x.value.trim())
        throw Error("Describe the application or answer the current question.");
      await api("copilot-sessions/" + session!.id + "/sources", "POST", {
        name: "Customer message",
        kind: "message",
        text: message.x.value,
      });
      const job = await api(
        "copilot-sessions/" + session!.id + "/turns",
        "POST",
        { profile_id: model.x.value },
      );
      await wait(job);
    });
    ask.disabled = busy || caps.disabled || !profiles.length;
    const composer=el("section","","copilot-composer");
    composer.append(message.wrap,ask);
    panel.insertBefore(composer,panel.children[3]||null);
    if (busy) {
      const status = el(
        "p",
        "Copilot is working. Watch the activity indicator above. Accepted inputs are unchanged.",
      );
      status.setAttribute("role", "status");
      composer.append(
        status,
        button("Cancel assistant operation", async () => {
          await api("jobs/" + jobId + "/cancel", "POST", {});
        }),
      );
    }
    const files = el("details");
    files.append(el("summary", "Add document text or telemetry"));
    const file = document.createElement("input");
    file.type = "file";
    file.accept = ".txt,.csv,.json";
    file.setAttribute("aria-label", "Document text or telemetry file");
    files.append(
      file,
      el(
        "p",
        "Supported: UTF-8 text, CSV and JSON up to 32 KB. Export PDF or Word content as text first. Uploaded content is untrusted evidence and never changes inputs automatically.",
      ),
      button("Attach source", async () => {
        const f = file.files?.[0];
        if (!f || f.size > 32000 || !/[.](txt|csv|json)$/i.test(f.name))
          throw Error("Choose a supported file up to 32 KB.");
        await api("copilot-sessions/" + session!.id + "/sources", "POST", {
          name: f.name,
          kind: f.name.endsWith(".txt") ? "document" : "telemetry",
          text: await f.text(),
        });
        await refresh();
      }),
    );
    panel.append(files);
    const sourceList = el("details");
    sourceList.append(el("summary", "Source register"));
    for (const s of history.sources)
      sourceList.append(
        el("p", s.data.name + " · " + s.id),
        el("pre", s.data.text),
      );
    panel.append(sourceList);
    const mcp = profiles.filter((p: J) => p.data.provider === "mcp");
    if (mcp.length) {
      const block = el("details");
      block.append(el("summary", "Import from approved MCP tool"));
      const target = select(
        "MCP connection",
        mcp.map((p: J) => [p.id, p.data.name]),
      );
      const tool = input("Approved read-only tool name"),
        args = input("Tool arguments JSON", "{}", true);
      block.append(
        target.wrap,
        tool.wrap,
        args.wrap,
        button("Retrieve tool data", async () => {
          await wait(
            await api(
              "copilot-sessions/" + session!.id + "/mcp-import",
              "POST",
              {
                profile_id: target.x.value,
                tool: tool.x.value,
                arguments: JSON.parse(args.x.value),
              },
            ),
          );
        }),
      );
      panel.append(block);
    }
    const manual = el("details");
    manual.append(
      el("summary", "Create a structured proposal without a model"),
    );
    const payload = input(
      "Proposal JSON",
      JSON.stringify(
        {
          question: "",
          changes: [
            {
              field: "components",
              value: [
                {
                  name: "Customer assistant",
                  pattern: "direct",
                  location: "local",
                  rate: "",
                  retrieval: "none",
                },
              ],
              basis: "planning_assumption",
              source_id: "",
              quote: "",
              reason: "Review the architecture and enter measured demand.",
            },
          ],
        },
        null,
        2,
      ),
      true,
    );
    manual.append(
      payload.wrap,
      button("Validate proposal", async () => {
        await api(
          "copilot-sessions/" + session!.id + "/proposals",
          "POST",
          JSON.parse(payload.x.value),
        );
        await refresh();
      }),
    );
    panel.append(manual);
    if (me.role === "admin")
      panel.append(
        el("p", "Manage connections using AI connections in the navigation."),
      );
  }
  await refresh();
  const pending=history.jobs.find((job:J)=>["queued","running","cancel_requested"].includes(job.data.state));
  if(pending)void wait(pending).catch(e=>{error=(e as Error).message;draw();});
}
export async function mountConnections(host: HTMLElement, api: API) {
  const me = await api("me");
  host.replaceChildren();
  host.append(
    el("h1", "AI connections"),
    el(
      "p",
      "Model services generate proposals. MCP servers supply approved tools and knowledge. Neither connection can modify accepted workload inputs.",
    ),
  );
  if (me.role !== "admin") {
    host.append(
      el("p", "Ask your administrator to configure approved connections."),
    );
    return;
  }
  const status = el("p");
  status.setAttribute("role", "status");
  host.append(status);
  const run = (label: string, fn: () => Promise<void>) => {
    const b = el("button", label) as HTMLButtonElement;
    b.onclick = async () => {
      b.disabled = true;
      try {
        await fn();
      } catch (e) {
        status.textContent = (e as Error).message;
      } finally {
        b.disabled = false;
      }
    };
    return b;
  };
  const profiles = await api("copilot-profiles");
  for (const p of profiles) {
    const row = el("section", "", "panel");
    row.append(
      el("h2", p.data.name),
      el(
        "p",
        `${p.data.provider} · ${p.data.model} · ${p.data.health} · ${p.data.data_policy} data policy`,
      ),
      run("Test " + p.data.name, async () => {
        const j = await api("copilot-profiles/" + p.id + "/test", "POST", {});
        status.textContent = "Testing connection…";
        for (let i = 0; i < 180; i++) {
          await new Promise((r) => setTimeout(r, 500));
          const x = await api("jobs/" + j.id);
          if (!["queued", "running"].includes(x.data.state)) {
            status.textContent = JSON.stringify(x.data, null, 2);
            return;
          }
        }
        status.textContent = "Test still running. Job " + j.id;
      }),
      run("Disable " + p.data.name, async () => {
        await api("copilot-profiles/" + p.id + "/disable", "POST", {});
        await mountConnections(host, api);
      }),
    );
    host.append(row);
  }
  const defaults: Record<string, J> = {
    openai: { origin: "https://api.openai.com", path: "/v1/chat/completions" },
    anthropic: { origin: "https://api.anthropic.com", path: "/v1/messages" },
    deepseek: { origin: "https://api.deepseek.com", path: "/chat/completions" },
    xai: { origin: "https://api.x.ai", path: "/v1/chat/completions" },
    gateway: {
      origin: "https://gateway.example.com",
      path: "/v1/chat/completions",
    },
    mcp: { origin: "https://mcp.example.com", path: "/mcp" },
  };
  const provider = document.createElement("select");
  provider.setAttribute("aria-label", "Provider");
  for (const name of Object.keys(defaults)) {
    const o = document.createElement("option");
    o.value = name;
    o.textContent = name;
    provider.append(o);
  }
  host.append(provider);
  const name = input("Connection name"),
    origin = input("Origin", defaults.openai.origin),
    path = input("API path", defaults.openai.path),
    model = input("Model identifier"),
    secret = input(
      "Backend secret environment variable",
      "ANUBIS_AI_KEY_PRIMARY",
    );
  provider.onchange = () => {
    origin.x.value = defaults[provider.value].origin;
    path.x.value = defaults[provider.value].path;
  };
  host.append(name.wrap, origin.wrap, path.wrap, model.wrap, secret.wrap);
  const reasoningLabel = el("label", "DeepSeek reasoning effort");
  const reasoning = document.createElement("select");
  reasoning.setAttribute("aria-label", "DeepSeek reasoning effort");
  for (const value of ["disabled", "low", "high"]) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    reasoning.append(option);
  }
  reasoningLabel.append(reasoning);
  host.append(
    reasoningLabel,
    el(
      "p",
      "Reasoning applies only to DeepSeek. It may improve extraction at additional latency and token cost. Each setting requires its own qualification. Existing connections retain their setting.",
    ),
  );
  const corporate = el("label", "Approved to process corporate data"),
    cb = document.createElement("input");
  cb.type = "checkbox";
  corporate.prepend(cb);
  host.append(
    corporate,
    el(
      "p",
      "This declaration must match your deployment policy. Corporate/private origins also require the server-side ANUBIS_AI_ALLOWED_ORIGINS allowlist. Never paste an API key into chat or these fields. Set the named secret in the backend environment and restart the service.",
    ),
  );
  const tools = input("Approved MCP tools JSON", "[]", true);
  host.append(
    tools.wrap,
    el(
      "p",
      "For MCP use records with name, schema_digest and read_only true. Test discovery first, then create a profile with reviewed tool digests. Newly discovered tools are never automatically permitted.",
    ),
  );
  host.append(
    run("Save connection", async () => {
      await api("copilot-profiles", "POST", {
        name: name.x.value,
        provider: provider.value,
        origin: origin.x.value,
        path: path.x.value,
        model: model.x.value,
        secret_env: secret.x.value,
        enabled: true,
        max_turns: 20,
        max_output_tokens: 8192,
        ...(provider.value === "deepseek"
          ? { reasoning_effort: reasoning.value }
          : {}),
        data_policy: cb.checked ? "corporate" : "public",
        ...(provider.value === "mcp"
          ? { protocol: "2025-06-18", tools: JSON.parse(tools.x.value) }
          : {}),
      });
      await mountConnections(host, api);
    }),
  );
}
