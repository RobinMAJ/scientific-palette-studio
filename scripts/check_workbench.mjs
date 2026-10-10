// Offline unit checks of our own HTML's pure color/export helpers; no browser/UI automation.
import fs from 'node:fs/promises';
import path from 'node:path';
import vm from 'node:vm';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const html=await fs.readFile(path.join(root,'examples/demo/palette-workbench.html'),'utf8');
const data=JSON.parse(html.split('<script id="payload" type="application/json">')[1].split('</script>')[0]);
const source=html.split('<script>')[1].split('</script>')[0].split("$('download-kit').onclick")[0];
const context=vm.createContext({structuredClone,TextEncoder,Blob,Uint8Array,DataView,Math,JSON,Array,Object,Number,Map,
 document:{getElementById(id){assert.equal(id,'payload');return {textContent:JSON.stringify(data)}}}});
new vm.Script(source+"\nglobalThis.helpers={gradients,zip,pal,palette256,cardSVG,sourceJSON,lab,fromLab};").runInContext(context);
const main=data.palette.main.map(c=>c.hex), generated=context.helpers.gradients(main);
assert.equal(generated.length,data.palette.gradients.length);
let maxError=0;
for(let i=0;i<generated.length;i++)for(let j=0;j<257;j++){
 const expected=data.palette.gradients[i].colors[j],actual=generated[i].colors[j];
 for(let k of [1,3,5])maxError=Math.max(maxError,Math.abs(parseInt(actual.slice(k,k+2),16)-parseInt(expected.slice(k,k+2),16)));
}
assert.ok(maxError<=1,'Python/JavaScript gradient mismatch');
for(let i=0;i<main.length;i++)assert.equal(generated[i].colors[128],main[i]);
assert.equal(context.helpers.pal(main).split(/\r?\n/)[2],String(main.length));
assert.equal(context.helpers.palette256(generated.at(-1)).length,256);
const changed=[...main];changed[0]='#AA3344';assert.equal(context.helpers.gradients(changed)[0].colors[128],'#AA3344');
assert.ok(context.helpers.cardSVG().includes('<linearGradient'));
await fs.mkdir(path.join(root,'.build'),{recursive:true});
for(const [name,parts]of [['browser-theme.thmx',data.themeParts],['browser-toolkit.pptx',data.pptxParts]]){
 const blob=context.helpers.zip(parts);await fs.writeFile(path.join(root,'.build',name),new Uint8Array(await blob.arrayBuffer()));
}
console.log(JSON.stringify({offline_helpers:'passed',gradient_max_rgb_difference:maxError,
 native_zip_files:['browser-theme.thmx','browser-toolkit.pptx'],browser_ui_tested:false},null,2));
