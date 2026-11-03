import assert from 'node:assert/strict';
import {systemDiagram} from '../ui/dist/system-diagram.js';
for (const pattern of ['direct','retrieval','agent','batch','training','stream','generation','adaptation','other']) {
 const svg=systemDiagram({pattern,name:'Example <application>',location:'local',rate:'100',retrieval:'external'});
 assert.ok(svg.includes('role="img"'));assert.ok(svg.includes('marker-end='));assert.ok(svg.includes('AI FACTORY COMPUTE'));
 assert.ok(svg.includes('Example &lt;application&gt;'));assert.ok(!svg.includes('Example <application>'));
 assert.ok(svg.includes('Data retained in this factory'));
}
assert.match(systemDiagram({pattern:'direct',location:'external'}),/COMPUTE OUTSIDE THIS AI FACTORY/);
assert.match(systemDiagram({pattern:'direct',location:'unknown'}),/COMPUTE LOCATION — to confirm/);
assert.match(systemDiagram({pattern:'retrieval',retrieval:'external'}),/Outside this AI Factory/);
assert.ok(!systemDiagram({pattern:'agent',retrieval:'none'}).includes('Tools / search service'));
assert.match(systemDiagram({pattern:'other'}),/GPU solver/);
assert.ok(!systemDiagram({pattern:'other'}).includes('2,000 preset'));
console.log('System diagram: all patterns, scope, measurement legend and escaping PASS');

assert.match(systemDiagram({pattern:'retrieval',retrieval:'local'}),/Inside this AI Factory/);
assert.match(systemDiagram({pattern:'retrieval',retrieval:'unknown'}),/Service location to confirm/);

assert.match(systemDiagram({pattern:"retrieval",retrieval:"external"}),/e.g. customer search cluster or cloud search/);
for (const pattern of ['stream','generation','adaptation']) {
 assert.ok(!systemDiagram({pattern,model:'dense8b'}).includes('dense8b'));
 assert.match(systemDiagram({pattern,sizing_method:'reference',reference_demand:'300',reference_unit:'frames',reference_gpus:'8'}),/300 frames\/s/);
 assert.match(systemDiagram({pattern,sizing_method:'reference',reference_gpus:'8'}),/8 GPUs per independent group/);
}
