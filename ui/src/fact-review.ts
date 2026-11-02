type J = Record<string, any>;
const node = (tag: string, text = "") => {
  const e = document.createElement(tag);
  e.textContent = text;
  return e;
};
export function factReview(proposal: J): HTMLElement {
  const section = node("section");
  section.className = "fact-review";
  section.append(
    node("h4", "Customer statements → reviewed facts → sizing inputs"),
  );
  section.append(
    node(
      "p",
      "These facts and their translations are reviewed together. Reported means stated in a source, not independently measured. Assumed values require your explicit acceptance.",
    ),
  );
  if (proposal.partial) {
    const warning = node("div");
    warning.className = "warning";
    warning.append(
      node("strong", "Partial extraction — excluded facts need review"),
      node("p", proposal.recovery_notice),
    );
    for (const rejected of proposal.rejected_facts || [])
      warning.append(
        node(
          "p",
          `${rejected.fact?.activity || "Activity"}: ${rejected.fact?.concept || "unknown field"}. ${rejected.error?.error?.message || "Invalid fact"}`,
        ),
      );
    section.append(warning);
  }
  const table = node("table");
  const header = node("tr");
  for (const t of [
    "Activity and fact",
    "Original value and period",
    "Evidence",
    "Sizing translation",
  ])
    header.append(node("th", t));
  table.append(header);
  for (const f of proposal.facts) {
    const row = node("tr");
    const original = f.value
      ? `${f.value} ${f.unit}${f.period_value ? " per " + f.period_value + " " + f.period_unit : ""}`
      : "Unknown";
    row.append(
      node("td", `${f.activity}: ${f.concept.replaceAll("_", " ")}`),
      node("td", original),
    );
    const evidence = node("td", f.status);
    if (f.quote) {
      const source = node("details");
      source.append(
        node("summary", "View source statement"),
        node("p", f.quote),
      );
      evidence.append(source);
    } else evidence.append(node("p", "No supporting statement"));
    row.append(evidence);
    const matches = proposal.trace.filter(
      (t: J) => t.activity === f.activity && t.concept === f.concept,
    );
    row.append(
      node(
        "td",
        matches
          .map((t: J) => `${t.field}: ${t.value} ${t.unit}. ${t.rule}`)
          .join("\n") || "Context or architecture evidence",
      ),
    );
    table.append(row);
  }
  section.append(table);
  if (proposal.conflicts.length) {
    const warning = node("div");
    warning.className = "warning";
    warning.append(node("strong", "Changes to previously accepted facts"));
    for (const c of proposal.conflicts)
      warning.append(
        node(
          "p",
          `${c.previous.activity}: ${c.previous.concept}. Previously ${c.previous.value} ${c.previous.unit}. Proposed ${c.proposed.value} ${c.proposed.unit}. Confirm the replacement or discard this proposal.`,
        ),
      );
    section.append(warning);
  }
  const trace = node("details");
  trace.append(node("summary", "Why this architecture and these values?"));
  for (const t of proposal.trace)
    trace.append(
      node(
        "p",
        `${t.activity}: ${t.field} = ${t.value} ${t.unit || ""}. Rule: ${t.rule}.`,
      ),
    );
  trace.append(
    node(
      "p",
      `Knowledge ${proposal.knowledge_version}. Rules ${proposal.rules_version}.`,
    ),
  );
  section.append(trace);
  section.append(
    node(
      "p",
      proposal.ready_for_estimate
        ? "Essential inputs are ready for review and calculation."
        : "More information is needed. You may accept known facts now and continue discovery. The builder remains available for explicitly reviewed planning estimates.",
    ),
  );
  return section;
}
export function manualFactForm(
  caps: J,
  session: J,
  submit: (payload: J, source: string) => Promise<void>,
): HTMLElement {
  const box = node("details");
  box.append(node("summary", "Enter or correct a fact without a model"));
  const form = node("div");
  box.append(form);
  const field = (label: string, values?: string[]) => {
    const wrap = node("label", label);
    wrap.className = "field";
    const control = document.createElement(values ? "select" : "input") as
      | HTMLInputElement
      | HTMLSelectElement;
    control.setAttribute("aria-label", label);
    if (values)
      for (const v of values) {
        const o = document.createElement("option");
        o.value = v;
        o.textContent = v.replaceAll("_", " ");
        control.append(o);
      }
    wrap.append(control);
    form.append(wrap);
    return control;
  };
  const activity = field("Business activity or Factory");
  activity.value =
    session.data.facts?.find((f: J) => f.activity !== "Factory")?.activity ||
    session.data.input.components[0]?.name ||
    "";
  const concept = field("Fact to describe", Object.keys(caps.fact_definitions));
  const value = field("Fact value");
  const unit = field("Measurement unit");
  const period = field("Measured period value");
  const periodUnit = field("Measured period unit", [
    "",
    "s",
    "min",
    "hour",
    "day",
  ]);
  const status = field("Evidence status", ["reported", "assumed", "unknown"]);
  const help = node("p");
  help.className = "field-definition";
  form.append(help);
  const update = () => {
    const d = caps.fact_definitions[concept.value];
    help.textContent =
      d.kind === "quantity"
        ? `Allowed units: ${d.units.join(", ")}. Preserve the original measurement. Requests, per-user requests and daily transfers need a period. Unknown means unspecified, not zero.`
        : `Allowed values: ${(d.values || ["supported model preset"]).join(", ")}. Local means inside this AI Factory. External means outside this AI Factory, such as an existing customer cluster or hosted service.`;
    unit.value = d.units?.[0] || "";
    value.value = "";
    period.value = "";
    periodUnit.value = "";
  };
  concept.onchange = update;
  update();
  form.append(
    node(
      "p",
      "Use measured traffic when available. To estimate from people, record demand basis = users, active users, and requests per user with its period. Population is context only. Record multiple user groups as distinct activities only when their traffic does not overlap.",
    ),
  );
  const button = node(
    "button",
    "Validate fact for review",
  ) as HTMLButtonElement;
  button.type = "button";
  button.onclick = async () => {
    button.disabled = true;
    try {
      const f = {
        activity: activity.value,
        concept: concept.value,
        value: status.value === "unknown" ? "" : value.value,
        unit: unit.value,
        period_value: period.value,
        period_unit: periodUnit.value,
        status: status.value,
        source_id: "",
        quote: "",
      };
      const statement = `Consultant ${status.value}: ${activity.value}. ${concept.value} = ${f.value} ${f.unit}${f.period_value ? " per " + f.period_value + " " + f.period_unit : ""}.`;
      await submit({ facts: [f] }, statement);
    } finally {
      button.disabled = false;
    }
  };
  form.append(button);
  return box;
}

export function demandForm(
  session: J,
  submit: (payload: J, source: string) => Promise<void>,
): HTMLElement {
  const box = node("details");
  box.append(node("summary", "Describe demand using measurements or users"));
  const wrap = node("div");
  box.append(wrap);
  const fields: Record<string, HTMLInputElement | HTMLSelectElement> = {};
  const add = (key: string, title: string, options?: string[]) => {
    const label = node("label", title);
    label.className = "field";
    const x = document.createElement(options ? "select" : "input") as
      | HTMLInputElement
      | HTMLSelectElement;
    x.setAttribute("aria-label", title);
    if (options)
      for (const v of options) {
        const o = document.createElement("option");
        o.value = v;
        o.textContent = v;
        x.append(o);
      }
    label.append(x);
    wrap.append(label);
    fields[key] = x;
    return label;
  };
  add("activity", "Demand activity name");
  fields.activity.value =
    session.data.facts?.find((f: J) => f.activity !== "Factory")?.activity ||
    session.data.input.components[0]?.name ||
    "";
  add("route", "How will you describe demand?", [
    "Measured busy-period traffic",
    "Estimate from active users",
  ]);
  const traffic = add("count", "Requests counted in the busy period");
  const users = add("active", "Active users during the busy period");
  const frequency = add("frequency", "Requests per active user in the period");
  add("period", "Length of the measured period");
  fields.period.value = "1";
  add("unit", "Period unit", ["min", "hour", "day"]);
  add("status", "Measurement basis", ["reported", "assumed"]);
  const explanation = node(
    "p",
    "Obtain busy-period counts from application logs. For the user route, use people actually making requests and their request frequency. Total employees do not establish demand. Choose an explicit assumption when measurements are unavailable. The two routes replace each other and are never added automatically.",
  );
  wrap.append(explanation);
  const toggle = () => {
    const measured = fields.route.value === "Measured busy-period traffic";
    traffic.hidden = !measured;
    users.hidden = frequency.hidden = measured;
  };
  fields.route.onchange = toggle;
  toggle();
  const save = node(
    "button",
    "Review demand measurements",
  ) as HTMLButtonElement;
  save.type = "button";
  save.onclick = async () => {
    save.disabled = true;
    try {
      const measured = fields.route.value === "Measured busy-period traffic",
        activity = fields.activity.value,
        status = fields.status.value;
      const f = (
        concept: string,
        value: string,
        unit = "",
        period_value = "",
        period_unit = "",
      ) => ({
        activity,
        concept,
        value,
        unit,
        period_value,
        period_unit,
        status,
        source_id: "",
        quote: "",
      });
      const facts = measured
        ? [
            f("demand_basis", "measured_peak"),
            f(
              "requests_peak",
              fields.count.value,
              "request",
              fields.period.value,
              fields.unit.value,
            ),
          ]
        : [
            f("demand_basis", "users"),
            f("active_users", fields.active.value, "person"),
            f(
              "requests_per_user",
              fields.frequency.value,
              "request",
              fields.period.value,
              fields.unit.value,
            ),
          ];
      const statement = measured
        ? `Consultant ${status}: ${activity} measured busy-period traffic is ${fields.count.value} requests per ${fields.period.value} ${fields.unit.value}.`
        : `Consultant ${status}: ${activity} has ${fields.active.value} active users, each making ${fields.frequency.value} requests per ${fields.period.value} ${fields.unit.value}.`;
      await submit({ facts }, statement);
    } finally {
      save.disabled = false;
    }
  };
  wrap.append(save);
  return box;
}
