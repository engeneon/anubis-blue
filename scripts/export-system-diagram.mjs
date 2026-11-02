import {systemDiagram} from '../ui/dist/system-diagram.js';
import {writeFile} from 'node:fs/promises';
import {createRequire} from 'node:module';
const require=createRequire('/Users/trai/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp/package.json');
const sharp=require('sharp');
const svg=systemDiagram({name:'Alder Contact Services — message classification',pattern:'direct',location:'local',rate:'100',model:'dense8b',calls:'1'});
await writeFile('deliverables/usability/Alder_System_Architecture.svg',svg);
await sharp(Buffer.from(svg),{density:200}).png().toFile('deliverables/usability/Alder_System_Architecture.png');
