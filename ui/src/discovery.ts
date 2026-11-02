type J = Record<string, any>;
let catalog: J | null = null,
  step = 0,
  selected = 0,
  result: J | null = null;
let answers: J = {
  name: "",
  tenancy: "unknown",
  overlap: "unknown",
  activities: [],
};
const words: Record<string, string> = {
  unknown: "Not sure yet",
  yes: "Yes",
  no: "No",
  local: "In this AI factory",
  external: "An external provider",
  mixed: "Some here, some externally",
  one: "One model call",
  several_fixed: "Several calls, fixed workflow",
  variable: "It varies by task",
  interactive: "When users ask",
  continuous: "Continuously",
  scheduled: "At scheduled times",
  overnight: "Overnight",
  independent: "Independent activity",
  after: "After the earlier activity",
  alongside: "Alongside the earlier activity",
  conditional: "Only in some cases after the earlier activity",
  shared: "Sharing is allowed",
  dedicated: "Dedicated capacity required",
  single: "One organisation",
  multi: "Separate customers",
};
function e(tag: string, text = "") {
  const x = document.createElement(tag);
  x.textContent = text;
  return x;
}
function b(text: string, fn: () => void) {
  const x = e("button", text) as HTMLButtonElement;
  x.type = "button";
  x.onclick = fn;
  return x;
}
function field(
  label: string,
  value: string,
  change: (v: string) => void,
  options?: string[],
) {
  const w = e("div"),
    id = crypto.randomUUID(),
    l = e("label", label);
  l.setAttribute("for", id);
  let x: HTMLInputElement | HTMLSelectElement;
  if (options) {
    x = document.createElement("select");
    for (const v of options) {
      const o = e("option", words[v] || v) as HTMLOptionElement;
      o.value = v;
      x.append(o);
    }
    x.value = value;
  } else {
    x = document.createElement("input");
    x.value = value;
  }
  x.id = id;
  if (x instanceof HTMLInputElement) x.oninput = () => change(x.value);
  else x.onchange = () => change(x.value);
  w.append(l, x);
  return w;
}
export async function mountDiscovery(
  host: HTMLElement,
  api: (p: string, m?: string, b?: unknown) => Promise<any>,
  create: (w: J) => Promise<void>,
  existing?: J,
) {
  if (!catalog) catalog = await api("architecture-core");
  if (!host.isConnected) return;
  const cat = catalog!;
  if (existing) {
    answers = structuredClone(existing.answers);
    step = 0;
    selected = 0;
    result = null;
  }
  if (!answers.activities.length)
    answers.activities.push({
      name: "Main application",
      answers: {},
      location: "unknown",
      calls: "unknown",
      schedule: "unknown",
      relationship: "independent",
      sharing: "unknown",
    });
  const invalidate = () => {
    result = null;
  };
  function draw() {
    host.replaceChildren();
    host.append(
      e("h1", "Describe your application"),
      e(
        "p",
        "Answer in application terms. Anubis proposes the workload patterns and arrangement. you can leave uncertain answers open. This step describes the architecture. Quantitative sizing follows.",
      ),
    );
    const nav = e("nav");
    nav.setAttribute("aria-label", "Discovery steps");
    [
      "1 Customer and scope",
      "2 What happens",
      "3 Arrangement",
      "4 Review architecture",
    ].forEach((v, i) => {
      const x = b(v, () => {
        step = i;
        draw();
      });
      if (i === step) x.setAttribute("aria-current", "step");
      nav.append(x);
    });
    host.append(nav, e("p", `You are here: step ${step + 1} of 4`));
    const error = e("p");
    error.setAttribute("role", "alert");
    host.append(error);
    if (step === 0) {
      host.append(
        field("Customer workload name", answers.name, (v) => {
          answers.name = v;
          invalidate();
        }),
        field(
          "Who will use this factory?",
          answers.tenancy,
          (v) => {
            answers.tenancy = v;
            invalidate();
          },
          ["unknown", "single", "multi"],
        ),
        e(
          "p",
          "Use one activity for each distinct job or service. For example: customer assistant, nightly indexing, weekly model training. Do not add every software microservice.",
        ),
      );
      const core = e("details");
      core.append(e("summary", "Explore the eight common patterns"));
      for (const p of cat.patterns)
        core.append(e("h3", p.name), e("p", p.description + " " + p.sizing));
      host.append(core);
    }
    if (step === 1 || step === 2) {
      const nav = e("div");
      answers.activities.forEach((a: J, i: number) =>
        nav.append(
          b(a.name || `Activity ${i + 1}`, () => {
            selected = i;
            draw();
          }),
        ),
      );
      if (answers.activities.length < 16)
        nav.append(
          b("Add activity", () => {
            answers.activities.push({
              name: `Activity ${answers.activities.length + 1}`,
              answers: {},
              location: "unknown",
              calls: "unknown",
              schedule: "unknown",
              relationship: "independent",
              sharing: "unknown",
            });
            selected = answers.activities.length - 1;
            invalidate();
            draw();
          }),
        );
      host.append(nav);
      const a = answers.activities[selected];
      host.append(
        field("Activity name", a.name, (v) => {
          a.name = v;
          invalidate();
        }),
      );
      if (step === 1) {
        for (const q of cat.questions) {
          const w = field(
            q.label,
            a.answers[q.id] || "unknown",
            (v) => {
              a.answers[q.id] = v;
              invalidate();
            },
            q.options,
          );
          w.className = "discovery-question";
          const help = e("details");
          help.append(
            e("summary", "Why we ask and how to find out"),
            e("p", q.why),
            e("p", "Where to find it: " + q.obtain),
            e(
              "p",
              "If uncertain, keep “Not sure yet”. Anubis will list this as a follow-up, not assume “No”.",
            ),
          );
          w.append(help);
          host.append(w);
        }
      } else {
        for (const q of cat.modifiers) {
          if (q.id === "relationship" && selected === 0) continue;
          const w = field(
            q.label,
            a[q.id] || "unknown",
            (v) => {
              a[q.id] = v;
              invalidate();
              draw();
            },
            q.options,
          );
          w.append(e("p", q.why + " " + q.obtain));
          host.append(w);
        }
        if (selected > 0 && a.relationship !== "independent") {
          const w = field(
            "Earlier activity",
            String(a.predecessor ?? 0),
            (v) => {
              a.predecessor = Number(v);
              invalidate();
            },
            answers.activities
              .slice(0, selected)
              .map((_: J, i: number) => String(i)),
          );
          const sel = w.querySelector("select")!;
          [...sel.options].forEach(
            (o, i) => (o.textContent = answers.activities[i].name),
          );
          if (a.predecessor === undefined) a.predecessor = 0;
          host.append(w);
        }
        host.append(
          field(
            "Can different activities be busy at the same time?",
            answers.overlap,
            (v) => {
              answers.overlap = v;
              invalidate();
            },
            ["unknown", "yes", "no"],
          ),
          e(
            "p",
            "“After” describes a dependency within a task. Many tasks may still overlap. Only choose “No” when the operating schedule prevents overlap.",
          ),
        );
      }
    }
    if (step === 3) {
      host.append(
        b("Discover architecture", async () => {
          try {
            result = await api("characterizations", "POST", answers);
            draw();
          } catch (err) {
            error.textContent = (err as Error).message;
          }
        }),
      );
      if (result) {
        host.append(
          e("h2", "Proposed workload architecture"),
          e("p", result.arrangement_note),
        );
        for (const a of result.activities) {
          const p = e("section");
          p.className = "panel";
          p.append(
            e("h3", a.name),
            e(
              "p",
              a.patterns.length
                ? a.patterns
                    .map(
                      (m: J) =>
                        cat.patterns.find((p: J) => p.id === m.id)?.name,
                    )
                    .join(" + ")
                : "No core pattern confirmed",
            ),
          );
          const flow = e("ol");
          flow.className = "discovery-flow";
          for (const node of a.flow) flow.append(e("li", node));
          p.append(
            flow,
            e(
              "p",
              `Runs: ${words[a.modifiers.schedule]}. Location: ${words[a.modifiers.location]}. Capacity: ${words[a.modifiers.sharing]}.`,
            ),
            e("p", a.sizing_support),
          );
          host.append(p);
        }
        for (const edge of result.relationships) {
          const names = (id: string) =>
            result!.activities.find((a: J) => a.id === id).name;
          host.append(
            e(
              "p",
              `${names(edge.to)}: ${words[edge.kind]} — ${names(edge.from)}`,
            ),
          );
        }
        host.append(e("h2", "Questions to resolve"));
        if (!result.questions.length)
          host.append(
            e(
              "p",
              "Architecture questions answered. Model, volume and performance inputs are still needed for sizing.",
            ),
          );
        for (const q of result.questions) host.append(e("p", "• " + q));
        host.append(
          b("Download characterisation", () => {
            const blob = new Blob([JSON.stringify(result, null, 2)], {
                type: "application/json",
              }),
              url = URL.createObjectURL(blob),
              link = e("a") as HTMLAnchorElement;
            link.href = url;
            link.download = "anubis-characterisation.json";
            link.click();
            URL.revokeObjectURL(url);
          }),
        );
        host.append(
          e(
            "p",
            "Check the proposed description with the customer. Saving creates a new engagement with these answers and unresolved activities. It does not replace an existing estimate or claim a GPU count.",
          ),
          b("Confirm description and create engagement", async () => {
            try {
              await create(result!.workload);
            } catch (err) {
              error.textContent = (err as Error).message;
            }
          }),
        );
      }
    }
    const controls = e("div");
    if (step > 0)
      controls.append(
        b("Previous", () => {
          step--;
          draw();
        }),
      );
    if (step < 3)
      controls.append(
        b("Continue", () => {
          step++;
          draw();
        }),
      );
    controls.append(
      b("Start a separate discovery", () => {
        answers = {
          name: "",
          tenancy: "unknown",
          overlap: "unknown",
          activities: [
            {
              name: "Main application",
              answers: {},
              relationship: "independent",
            },
          ],
        };
        result = null;
        step = 0;
        selected = 0;
        draw();
      }),
    );
    host.append(controls);
  }
  draw();
}
