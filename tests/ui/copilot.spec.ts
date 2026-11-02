import { test, expect } from "@playwright/test";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
const token = "ui-test-token-not-a-production-secret";
const evidence = "implementation/copilot/gui";
test("random scenario assisted discovery review sizing and handoff", async ({
  page,
  request,
}) => {
  test.setTimeout(120000);
  mkdirSync(evidence, { recursive: true });
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  page.setDefaultTimeout(12000);
  const headers = { Authorization: "Bearer " + token };
  const origin = readFileSync(
    "test-results/copilot-fixture-origin.txt",
    "utf8",
  );
  const post = async (path: string, data: unknown) => {
    const r = await request.post("/api/v1/" + path, { headers, data });
    expect(r.ok(), await r.text()).toBeTruthy();
    return r.json();
  };
  const profile = await post("copilot-profiles", {
    name: "Local validation connection",
    provider: "gateway",
    origin,
    path: "/v1/chat/completions",
    model: "fixture",
    secret_env: "ANUBIS_AI_KEY_UI_FIXTURE",
    enabled: true,
    max_turns: 20,
    max_output_tokens: 2048,
    data_policy: "corporate",
  });
  const job = await post("copilot-profiles/" + profile.id + "/test", {});
  await expect
    .poll(async () => {
      const r = await request.get("/api/v1/jobs/" + job.id, { headers });
      return (await r.json()).data.state;
    })
    .toBe("succeeded");
  const scenario = JSON.parse(
    readFileSync("implementation/copilot/random-scenario.json", "utf8"),
  ).scenario;
  expect(scenario.id).toBe("S03");
  await page.goto("/");
  await page.getByLabel("Access token").fill(token);
  await page.getByRole("button", { name: "Open workspace" }).click();
  await page
    .getByRole("button", { name: "Consultant Copilot", exact: true })
    .click();
  await page.getByLabel("Customer workload name").fill(scenario.name);
  await page.getByRole("button", { name: "Start assisted engagement" }).click();
  await page.getByLabel("Model connection").selectOption(profile.id);
  await page
    .getByLabel("What should we know about the workload?")
    .fill(scenario.story);
  await page.getByRole("button", { name: "Ask copilot", exact: true }).click();
  await expect(page.getByRole("region",{name:"Copilot activity"})).toBeVisible();
  await expect(page.getByRole("button",{name:"Ask copilot",exact:true})).toBeDisabled();
  await expect(page.locator("[data-copilot-elapsed]")).toContainText("Elapsed:");
  await page.screenshot({path:evidence+"/00-copilot-working.png",fullPage:true});

  await expect(
    page.getByRole("heading", { name: "Input proposal — proposed" }),
  ).toBeVisible();
  await expect(
    page.getByText("Will the model or computation run inside this AI Factory", {
      exact: false,
    }),
  ).toBeVisible();
  await page.screenshot({
    path: evidence + "/01-architecture-proposal.png",
    fullPage: true,
  });
  await page
    .getByLabel("What should we know about the workload?")
    .fill(
      "For this fictional test, assume a measured peak of 30 requests per minute. Use 12 model calls per case as a planning envelope. Search is not required. Assume the model runs inside this AI Factory using dense8b, with 2000 input tokens and 500 output tokens per call.",
    );
  await page.getByRole("button", { name: "Ask copilot", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Input proposal — proposed" }),
  ).toHaveCount(2);
  const card = page
    .locator("section.panel")
    .filter({
      hasText:
        "Review the facts and explicit assumptions, then calculate requirements.",
    })
    .first();
  await card
    .getByLabel(
      "I reviewed the selected values and accept the planning assumptions.",
    )
    .check();
  await card
    .getByRole("button", { name: "Apply selected", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Input proposal — applied" }),
  ).toBeVisible();
  await expect(
    page
      .getByRole("heading", { name: "Your application architecture" })
      .first(),
  ).toBeVisible();
  await page.screenshot({
    path: evidence + "/02-reviewed-architecture.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Review and calculate GPU estimate" })
    .click();
  await expect(page.getByRole("heading", { name: "Review your first estimate" })).toBeVisible();
  await expect(page.getByRole("button", { name: "4 Review and estimate", exact: true })).toHaveAttribute("aria-current", "step");
  await page.getByLabel("Use these planning assumptions").check();
  await page
    .getByRole("button", { name: "Calculate estimate", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Workload analysis" }),
  ).toBeVisible();
  await page.screenshot({
    path: evidence + "/03-sizing-results.png",
    fullPage: true,
  });
  await page.getByRole("button", {name:"Continue to Design handoff",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Stage 4: prepare your design inputs"})).toBeVisible();
  await expect(page.getByRole("button", {name:"Back to calculation results"})).toBeVisible();
  await page.getByRole("button", {name:"Prepare projection",exact:true}).click();
  await expect(page.getByRole("heading", {name:"AI Factory design executive summary"})).toBeVisible();
  await expect(page.getByRole("button", {name:"Download executive summary"})).toBeVisible();
  await page.screenshot({ path: evidence + "/04-handoff.png", fullPage: true });
  await page.getByLabel("Completion notes",{exact:true}).fill("Pilot requirements delivered for architecture design.");
  await page.getByLabel("I confirm that these selected requirements are delivered.",{exact:true}).check();
  await page.getByRole("button",{name:"Complete engagement",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Saved deliverables",exact:true})).toBeVisible();
  await expect(page.getByText("Pilot requirements delivered for architecture design.",{exact:false})).toBeVisible();
  await page.getByRole("button",{name:"Consultant Copilot",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Completed engagement — historical record",exact:true})).toBeVisible();
  await expect(page.getByRole("button",{name:"Ask copilot",exact:true})).toHaveCount(0);
  await page.screenshot({path:evidence+"/07-completed-history.png",fullPage:true});
  await page.getByRole("button",{name:"View saved deliverables or reopen",exact:true}).click();

  await page.reload();
  await page.getByRole("button",{name:"Cases",exact:true}).click();
  await expect(page.getByRole("table",{name:"Engagement status",exact:true})).toBeVisible();
  await expect(page.getByRole("columnheader",{name:"Current status",exact:true})).toBeVisible();
  await expect(page.locator(".engagement-row").filter({hasText:scenario.name})).toContainText("Completed · requirements delivered");
  await page.locator(".engagement-row").filter({hasText:scenario.name}).getByRole("button",{name:"View engagement",exact:true}).click();
  await expect(page.getByRole("button",{name:"Download complete engagement record",exact:true})).toBeVisible();
  const [deliveryDownload]=await Promise.all([page.waitForEvent('download'),page.getByRole("button",{name:"Download complete engagement record",exact:true}).click()]);
  const savedDelivery=JSON.parse(readFileSync((await deliveryDownload.path())!,"utf8"));
  expect(savedDelivery.data.notes).toBe("Pilot requirements delivered for architecture design.");
  expect(savedDelivery.data.projection_snapshot.result_id).toBe(savedDelivery.data.result_id);
  await page.getByRole("button",{name:"Reopen engagement for revisions",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Consultant Copilot",exact:true})).toBeVisible();
  await page.getByLabel("Model connection").selectOption(profile.id);
  await page.getByLabel("What should we know about the workload?").fill(scenario.story);
  await page.getByRole("button",{name:"Ask copilot",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Input proposal — proposed",exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Saved deliverables",exact:true}).click();
  await expect(page.getByRole("button",{name:"Download complete engagement record",exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Continue with Copilot",exact:true}).click();
  await expect(page.getByRole("button",{name:"Ask copilot",exact:true})).toBeVisible();

  await page
    .getByRole("button", { name: "Consultant Copilot", exact: true })
    .click();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByLabel("Model connection")).toBeVisible();
  await page.screenshot({
    path: evidence + "/05-responsive.png",
    fullPage: true,
  });
  expect(errors).toEqual([]);
  writeFileSync(
    evidence + "/validation.json",
    JSON.stringify(
      {
        scenario: scenario.id,
        actual_gui: true,
        provider: "local fixture",
        live_interpretation_qualified: false,
        console_errors: errors,
        steps: [
          "discover",
          "clarify variable calls and peak",
          "review",
          "diagram",
          "compile",
          "engine facts",
          "handoff",
        ],
        new_measurements:
          "Fictional 30 requests/minute and 12 calls/case envelope",
      },
      null,
      2,
    ),
  );
});

test("Case A accepted facts lead directly to GPU estimate review", async ({ page, request }) => {
  const headers = { Authorization: "Bearer " + token };
  const post = async (path: string, data: unknown) => {
    const r = await request.post("/api/v1/" + path, { headers, data });
    expect(r.ok(), await r.text()).toBeTruthy();
    return r.json();
  };
  await page.goto("/");
  await page.getByLabel("Access token").fill(token);
  await page.getByRole("button", { name: "Open workspace" }).click();
  await page.getByRole("button", { name: "Consultant Copilot", exact: true }).click();
  await page.getByLabel("Customer workload name").fill("Case A document assistant navigation");
  const created = page.waitForResponse(r => r.url().endsWith("/copilot-sessions") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Start assisted engagement" }).click();
  const session = await (await created).json();
  const story = "A local answer model serves engineers using passages from an existing search system outside this AI Factory. The busiest hour has 2,400 questions. The external search system indexes a 4 TB document corpus. For this pilot, explicitly assume dense8b, 2,000 input tokens and 500 output tokens per call.";
  const source = await post(`copilot-sessions/${session.id}/sources`, {name:"Case A",kind:"message",text:story});
  const fact = (concept: string, value: string, unit="", period_value="", period_unit="", status="reported") => ({activity:"Document assistant",concept,value,unit,period_value,period_unit,status,source_id:source.id,quote:story});
  await post(`copilot-sessions/${session.id}/proposals`, {facts:[
    fact("text_model","yes"),fact("search","yes"),fact("compute_location","local"),fact("search_location","external"),fact("data_location","external"),fact("storage","4","TB"),fact("requests_peak","2400","request","1","hour"),fact("demand_basis","measured_peak"),fact("model","dense8b","","","","assumed"),fact("input_tokens","2000","token","","","assumed"),fact("output_tokens","500","token","","","assumed")
  ]});
  await page.getByRole("button", {name:"Refresh session",exact:true}).click();
  await page.getByLabel("I reviewed the selected values and accept the planning assumptions.").check();
  await page.getByRole("button", {name:"Apply selected",exact:true}).click();
  const next = page.locator("#copilot-next-step");
  await expect(next).toBeFocused();
  await expect(next.getByRole("button", {name:"Review and calculate GPU estimate"})).toBeVisible();
  const acceptedSession = await (await request.get(`/api/v1/copilot-sessions/${session.id}`, {headers})).json();
  const draftPath = `/api/v1/drafts/${acceptedSession.data.draft_id}`;
  const beforeView = await (await request.get(draftPath, {headers})).json();
  await page.getByRole("button", {name:"Open workload builder and calculate"}).click();
  await page.getByRole("button", {name:"Open advanced workload editor"}).click();
  await expect(page.getByRole("heading", {name:"Editing options"})).toBeVisible();
  expect(await (await request.get(draftPath, {headers})).json()).toEqual(beforeView);
  await page.getByLabel("Workload name",{exact:true}).fill("Case A renamed safely");
  await page.getByRole("button", {name:"Review assisted editing options"}).click();
  await page.getByRole("button", {name:"Return to assisted editing"}).click();
  await expect(page.getByRole("button", {name:"1 Choose application",exact:true})).toHaveAttribute("aria-current","step");
  await expect(page.getByLabel("Customer workload name",{exact:true})).toHaveValue("Case A renamed safely");
  await page.getByRole("button", {name:"Consultant Copilot",exact:true}).click();
  await next.getByRole("button", {name:"Review and calculate GPU estimate"}).click();
  await expect(page.getByRole("heading", {name:"Review your first estimate"})).toBeVisible();
  await expect(page.getByLabel("Use these planning assumptions")).not.toBeChecked();
  await page.getByLabel("Use these planning assumptions").check();
  await page.getByRole("button", {name:"Calculate estimate",exact:true}).click();
  await expect(page.getByRole("heading", {name:"Workload analysis"})).toBeVisible();
  await expect(page.getByText("HGX_B300", {exact:false}).first()).toBeVisible();
  await page.screenshot({path:evidence+"/06-case-a-gpu-results.png",fullPage:true});
  await page.getByRole("button", {name:"4. Design handoff",exact:true}).click();
  await expect(page.getByRole("heading", {name:"Design handoff",exact:true})).toBeVisible();
  await page.getByRole("button", {name:"Prepare projection",exact:true}).click();
  await expect(page.getByRole("heading", {name:"AI Factory design executive summary"})).toBeVisible();
  await page.getByRole("button", {name:"Back to calculation results",exact:true}).click();
  await expect(page.getByRole("heading", {name:"Workload analysis",exact:true})).toBeVisible();
  await page.getByRole("button",{name:"Workload builder",exact:true}).click();
  await page.getByRole("button",{name:"Open advanced workload editor"}).click();
  const beforeEdit = await (await request.get(draftPath,{headers})).json();
  await page.getByRole("navigation",{name:"Workload phases"}).getByRole("button").nth(2).click();
  await page.getByLabel("Compute efficiency fraction",{exact:true}).fill("0.42");
  page.once("dialog",d=>{expect(d.message()).toContain("/planning/compute_efficiency");return d.dismiss();});
  await page.getByRole("button",{name:"Save draft",exact:true}).click();
  await expect(page.getByText("Save cancelled. Your unsaved edits remain in the editor.",{exact:true})).toBeVisible();
  expect(await (await request.get(draftPath,{headers})).json()).toEqual(beforeEdit);
  page.once("dialog",d=>d.accept());
  await page.getByRole("button",{name:"Save draft",exact:true}).click();
  await expect.poll(async()=> (await (await request.get(draftPath,{headers})).json()).data.planning.compute_efficiency).toBe("0.42");
  const protectedOriginal = await (await request.get(draftPath,{headers})).json();
  await page.getByRole("button",{name:"Consultant Copilot",exact:true}).click();
  await expect(page.getByRole("heading",{name:"Your saved workload is protected"})).toBeVisible();
  await page.getByText("Review a separate assisted copy",{exact:true}).click();
  await page.getByRole("button",{name:"Create separate assisted copy",exact:true}).click();
  await expect(page.getByRole("button",{name:"1 Choose application",exact:true})).toBeVisible();
  expect(await (await request.get(draftPath,{headers})).json()).toEqual(protectedOriginal);

});

test("engagement deletion can be cancelled and restored", async ({page,request})=>{
 const headers={Authorization:"Bearer "+token};const response=await request.post('/api/v1/cases',{headers,data:{name:"Lifecycle deletion fixture"}});expect(response.ok()).toBeTruthy();
 await page.goto('/');await page.getByLabel('Access token').fill(token);await page.getByRole('button',{name:'Open workspace',exact:true}).click();
 await page.getByRole('button',{name:'Cases',exact:true}).click();
 const row=page.locator('.engagement-row').filter({hasText:'Lifecycle deletion fixture'});
 page.once('dialog',d=>d.dismiss());await row.getByRole('button',{name:'Delete engagement',exact:true}).click();await expect(row).toBeVisible();
 page.once('dialog',d=>d.accept());await row.getByRole('button',{name:'Delete engagement',exact:true}).click();await expect(row).toHaveCount(0);
 await page.getByRole('button',{name:'Show deleted engagements',exact:true}).click();await expect(row).toBeVisible();
 await row.getByRole('button',{name:'Restore engagement',exact:true}).click();await expect(row.getByRole('button',{name:'View engagement',exact:true})).toBeVisible();
});

test("specialist engagement concludes without a GPU result or handoff",async({page,request})=>{
 const headers={Authorization:'Bearer '+token};const post=async(path:string,data:unknown)=>{const r=await request.post('/api/v1/'+path,{headers,data});expect(r.ok(),await r.text()).toBeTruthy();return r.json();};
 await page.goto('/');await page.getByLabel('Access token').fill(token);await page.getByRole('button',{name:'Open workspace',exact:true}).click();await page.getByRole('button',{name:'Consultant Copilot',exact:true}).click();await page.getByLabel('Customer workload name').fill('Case C specialist closure');
 const created=page.waitForResponse(r=>r.url().endsWith('/copilot-sessions')&&r.request().method()==='POST');await page.getByRole('button',{name:'Start assisted engagement',exact:true}).click();const session=await(await created).json();
 const source=await post(`copilot-sessions/${session.id}/sources`,{name:'Case C',kind:'message',text:'A turbine manufacturer needs GPU fluid simulation. Solver throughput and memory measurements are unavailable.'});
 await post(`copilot-sessions/${session.id}/proposals`,{facts:[{activity:'Turbine simulation',concept:'simulation',value:'yes',unit:'',period_value:'',period_unit:'',status:'reported',source_id:source.id,quote:source.data.text}]});
 await page.getByRole('button',{name:'Refresh session',exact:true}).click();await page.getByRole('button',{name:'Review final status report',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Final status report preview',exact:true})).toBeVisible();await expect(page.getByText('No calculation result is available.',{exact:false})).toBeVisible();
 await page.getByLabel('Reason for concluding now',{exact:true}).fill('Obtain solver-specific benchmarks before further sizing.');await page.getByLabel('I confirm closure with a status report, without delivering a design handoff.',{exact:true}).check();await page.getByRole('button',{name:'Close with final status report',exact:true}).click();
 await expect(page.getByRole('button',{name:'Download final status report',exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Download design intake',exact:true})).toHaveCount(0);
 const [download]=await Promise.all([page.waitForEvent('download'),page.getByRole('button',{name:'Download final status report',exact:true}).click()]);expect(readFileSync((await download.path())!,'utf8')).toContain('Obtain solver-specific benchmarks');
 await page.reload();await page.getByRole('button',{name:'Cases',exact:true}).click();const row=page.locator('.engagement-row').filter({hasText:'Case C specialist closure'});await expect(row).toContainText('Closed · final status report');await row.getByRole('button',{name:'View engagement',exact:true}).click();await expect(page.getByRole('button',{name:'Download complete closure record',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Reopen engagement for revisions',exact:true}).click();await expect(page.getByRole('heading',{name:'Consultant Copilot',exact:true})).toBeVisible();
});

test("specialist calculation reaches report closure directly from stage four",async({page,request})=>{
 const headers={Authorization:'Bearer '+token};const post=async(path:string,data:unknown,version?:number)=>{const r=await request.post('/api/v1/'+path,{headers:{...headers,...(version?{'If-Match':String(version)}:{})},data});expect(r.ok(),await r.text()).toBeTruthy();return r.json();};
 const c=await post('cases',{name:'Case C stage four regression'});
 const workload=await post('guided-workloads',{name:c.data.name,accepted:true,tenancy:'single',overlap:'unknown',components:[{name:'Turbine fluid simulation',pattern:'other',location:'local',relationship:'independent'}],notes:'Solver-specific measurements unavailable'});
 const d=await post(`cases/${c.id}/drafts`,workload);const rev=await post(`drafts/${d.id}/freeze`,{},d.version);const job=await post('compilations',{revision_id:rev.id});
 await expect.poll(async()=>{const r=await request.get('/api/v1/jobs/'+job.id,{headers});return(await r.json()).data.state;}).toBe('succeeded');
 await page.goto('/');await page.getByLabel('Access token').fill(token);await page.getByRole('button',{name:'Open workspace',exact:true}).click();await page.getByRole('button',{name:'Cases',exact:true}).click();await page.locator('.engagement-row').filter({hasText:c.data.name}).getByRole('button',{name:'View engagement',exact:true}).click();
 await page.getByRole('button',{name:'Analysis',exact:true}).click();await page.getByRole('button',{name:'Continue to Design handoff',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Stage 4: conclude or continue discovery',exact:true})).toBeVisible();await expect(page.getByRole('button',{name:'Prepare projection',exact:true})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Continue gathering workload evidence',exact:true})).toBeVisible();await page.getByRole('button',{name:'Review final status report',exact:true}).click();
 await page.getByLabel('Reason for concluding now',{exact:true}).fill('Specialist benchmarking is needed before a valid design handoff.');await page.getByLabel('I confirm closure with a status report, without delivering a design handoff.',{exact:true}).check();await page.getByRole('button',{name:'Close with final status report',exact:true}).click();await expect(page.getByRole('button',{name:'Download final status report',exact:true})).toBeVisible();
});
