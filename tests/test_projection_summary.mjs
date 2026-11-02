import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {projectionSummary,projectionSummaryText} from '../ui/dist/projection-summary.js';
const p=JSON.parse(readFileSync('tests/fixtures/projection-narrative.json','utf8'));
const s=projectionSummaryText(p);
assert.equal(s,projectionSummaryText(structuredClone(p)));
for(const text of ['8 HGX B300 GPUs','256 GPUs','32 simultaneous copies','31 additional copies','not a validated tenant limit','73 kbit/s inbound','19 kbit/s outbound','Initial data-loading capacity remains unresolved','not recommended circuit sizes','No shared-storage tier','partial transfer','external reconciliation'])assert.ok(s.includes(text),text);
assert.ok(projectionSummary(p).every(i=>i.sources.length));
const empty=projectionSummaryText({});assert.ok(empty.includes('not established'));assert.ok(!empty.includes('undefined'));assert.ok(!empty.includes('NaN'));
const small=structuredClone(p);small.companion_requirements.initial_gpus=4;assert.ok(projectionSummaryText(small).includes('below the workload estimate'));
const zero=structuredClone(p);zero.companion_requirements.networks.external_customer_datacenter.initial_load_link_Gbps='0';assert.ok(projectionSummaryText(zero).includes('Initial-loading link lower bound: 0 Gbit/s'));assert.ok(!projectionSummaryText(zero).includes('Initial data-loading capacity remains unresolved'));
const changed=structuredClone(p);changed.companion_requirements.tenancy='multi';changed.companion_requirements.networks.storage.dedicated=false;assert.ok(projectionSummaryText(changed).includes('multiple tenants'));assert.ok(projectionSummaryText(changed).includes('separation must be confirmed'));
mkdirSync('implementation/copilot',{recursive:true});
writeFileSync('implementation/copilot/example-design-executive-summary.txt',s);
console.log('Projection narrative: determinism, source trace, anchor distinction, unknown/zero, shortfall and policy branches passed');

const range=structuredClone(p); range.companion_requirements.upside_gpus=8; range.companion_requirements.downside_gpus=24; assert.ok(projectionSummaryText(range).includes("8–24 GPUs"));
