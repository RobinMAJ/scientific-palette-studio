// Maintainer check: import and render our generated deck using Artifact Tool.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob,PresentationFile} from '@oai/artifact-tool';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const input=process.argv[2]||path.join(root,'examples/demo/powerpoint/palette-toolkit.pptx');
const out=process.argv[3]||path.join(root,'.build/demo-render');
await fs.mkdir(out,{recursive:true});
const p=await PresentationFile.importPptx(await FileBlob.load(input));
for(const [i,s]of p.slides.items.entries()){
 const b=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(out,`slide-${i+1}.png`),new Uint8Array(await b.arrayBuffer()));
}
console.log(JSON.stringify({slides:p.slides.items.length,output:out,native_powerpoint_tested:false}));
