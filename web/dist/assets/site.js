'use strict';
// All file bytes, rasterization, extraction and exports remain in the visitor's browser.
const sourceCanvas=$('source-canvas'),sourceCtx=sourceCanvas.getContext('2d',{willReadFrequently:true}),pending=new Map();
let extractWorker=null,workerId=0,busy=false,source=null,pdf=null,pdfTask=null,crop=null,startPoint=null,pdfModule=null;
function task(message,error=false){$('task-status').textContent=message;$('task-status').classList.toggle('error',error)}
function lock(value){busy=value;for(let id of ['extract','show-page','try-sample','clear-source','use-manual','file-input'])$(id).disabled=value;$('dropzone').setAttribute('aria-busy',String(value))}
function resetResult(){palette=structuredClone(original);$('results').hidden=true;status('')}
function samplePixels(canvas,rect){const r=rect||{x:0,y:0,w:canvas.width,h:canvas.height};return canvas.getContext('2d',{willReadFrequently:true}).getImageData(r.x,r.y,r.w,r.h).data}
async function runExtraction(pixels){
 const count=+ $('color-count').value,includeNeutrals=$('include-neutrals').checked;
 if(!extractWorker){extractWorker=new Worker('assets/extract-worker.mjs',{type:'module'});extractWorker.onmessage=e=>{let p=pending.get(e.data.id);if(!p)return;clearTimeout(p.timer);pending.delete(e.data.id);e.data.error?p.reject(Error(e.data.error)):p.resolve(e.data.result)};extractWorker.onerror=()=>{for(let p of pending.values()){clearTimeout(p.timer);p.reject(Error('The color worker could not start. Reload the page in a recent browser.'))}pending.clear();extractWorker.terminate();extractWorker=null}}
 return new Promise((resolve,reject)=>{const id=++workerId,timer=setTimeout(()=>{pending.delete(id);reject(Error('Color extraction took too long. Try a smaller crop.'))},30000);pending.set(id,{resolve,reject,timer});extractWorker.postMessage({id,pixels:pixels.buffer,count,includeNeutrals},[pixels.buffer])});
}
async function digest(data){if(!crypto.subtle)return null;const d=await crypto.subtle.digest('SHA-256',data);return [...new Uint8Array(d)].map(x=>x.toString(16).padStart(2,'0')).join('')}
function revealSource(){sourceCanvas.hidden=false;$('empty-preview').hidden=true;$('source-controls').hidden=false;$('file-name').textContent=source.name;$('source-label').textContent=pdf?`Page ${source.page} · drag to select a figure`:'Drag to select a figure';clearCrop();}
function clearCrop(){crop=null;startPoint=null;$('crop-overlay').hidden=true;$('clear-crop').hidden=true;$('crop-summary').textContent='Using the whole image.'}
function drawCrop(){if(!crop){$('crop-overlay').hidden=true;return}let r=sourceCanvas.getBoundingClientRect(),s=$('preview-stage').getBoundingClientRect(),e=$('crop-overlay');e.hidden=false;e.style.left=(r.left-s.left+crop.x/sourceCanvas.width*r.width)+'px';e.style.top=(r.top-s.top+crop.y/sourceCanvas.height*r.height)+'px';e.style.width=crop.w/sourceCanvas.width*r.width+'px';e.style.height=crop.h/sourceCanvas.height*r.height+'px';$('clear-crop').hidden=false;$('crop-summary').textContent=`Selection: ${crop.w} × ${crop.h} rendered pixels.`}
const point=e=>{const r=sourceCanvas.getBoundingClientRect();return {x:Math.min(sourceCanvas.width,Math.max(0,(e.clientX-r.left)/r.width*sourceCanvas.width)),y:Math.min(sourceCanvas.height,Math.max(0,(e.clientY-r.top)/r.height*sourceCanvas.height))}};
sourceCanvas.onpointerdown=e=>{if(busy)return;e.preventDefault();startPoint=point(e);sourceCanvas.setPointerCapture(e.pointerId)};
sourceCanvas.onpointermove=e=>{if(!startPoint)return;let p=point(e);crop={x:Math.floor(Math.min(p.x,startPoint.x)),y:Math.floor(Math.min(p.y,startPoint.y)),w:Math.ceil(Math.abs(p.x-startPoint.x)),h:Math.ceil(Math.abs(p.y-startPoint.y))};crop.w=Math.min(crop.w,sourceCanvas.width-crop.x);crop.h=Math.min(crop.h,sourceCanvas.height-crop.y);drawCrop()};
sourceCanvas.onpointerup=e=>{if(!startPoint)return;startPoint=null;if(!crop||crop.w<5||crop.h<5)clearCrop();else task('Figure selected. Click Extract colors to use this area.');if(sourceCanvas.hasPointerCapture(e.pointerId))sourceCanvas.releasePointerCapture(e.pointerId)};
sourceCanvas.onpointercancel=()=>clearCrop();window.addEventListener('resize',drawCrop);$('clear-crop').onclick=()=>{clearCrop();task('Selection cleared. Click Extract colors to use the whole image.')};
window.addEventListener('keydown',e=>{if(e.key==='Escape'&&crop)clearCrop()});
async function showPDFPage(page,canvas=sourceCanvas){
 if(!Number.isInteger(page)||page<1||page>pdf.numPages)throw Error(`Choose a page from 1 to ${pdf.numPages}.`);
 const p=await pdf.getPage(page),base=p.getViewport({scale:1}),scale=Math.min(2.2,1800/Math.max(base.width,base.height)),view=p.getViewport({scale});canvas.width=Math.ceil(view.width);canvas.height=Math.ceil(view.height);const c=canvas.getContext('2d',{willReadFrequently:true});await p.render({canvasContext:c,viewport:view,background:'#FFFFFF'}).promise;p.cleanup();
 if(canvas===sourceCanvas){source.page=page;$('pdf-page').value=page;revealSource()}
}
function applyPalette(colors,provenance,title){
 palette={schema_version:'1.0',generator_version:'web-1.0.0',title:title.slice(0,160),background:'#FFFFFF',main:colors.map((c,i)=>({id:`color-${String(i+1).padStart(2,'0')}`,hex:c,rgb:rgb(c),basis:provenance.basis})),gradients:gradients(colors),provenance,audit:audit(colors)};
 for(let key of Object.keys(original))delete original[key];Object.assign(original,structuredClone(palette));render();$('results').hidden=false;
 $('basis').textContent=`Main colors: ${provenance.basis} · Gradients: derived · sRGB${provenance.sources?.[0]?.page?' · PDF page '+provenance.sources[0].page:''}`;
}
async function extractCurrent(){
 if(!source)throw Error('Choose a source first.');
 task('Finding colors in the selected figure…');const result=await runExtraction(samplePixels(sourceCanvas,crop));
 const info={name:source.name,type:source.type,sha256:source.sha256,rendered_width:sourceCanvas.width,rendered_height:sourceCanvas.height,page:source.page||null,crop:crop?{...crop}:null};
 applyPalette(result.colors,{basis:source.demo?'original demonstration':'extracted',sources:[info],extraction:result,notes:['Main colors are representative rendered sRGB pixels. Gradients are derived, not extracted.','Rasterized PDFs, embedded color profiles, screenshots and antialiasing can change pixel colors.']},source.demo?'Mineral & molecular colors':source.name.replace(/\.[^.]+$/,'')+' · palette');
 task(`${result.colors.length} main colors found${result.colors.length<result.requested_colors?' (fewer distinct colors than requested)':''}. Your palette and downloads are ready below.`);
}
async function clearDocument(){if(pdfTask){const old=pdfTask;pdfTask=null;pdf=null;await old.destroy()}source=null;clearCrop();sourceCanvas.width=1;sourceCanvas.height=1;sourceCanvas.hidden=true;$('empty-preview').hidden=false;$('source-controls').hidden=true;$('pdf-controls').hidden=true;$('source-label').textContent='Choose a reference to begin';$('file-input').value='';resetResult()}
async function loadFile(file){
 if(busy){task('Finishing the current file. Please try again in a moment.');return}
 lock(true);try{
 if(!file||file.size===0)throw Error('Choose a non-empty file.');if(file.size>30*1024*1024)throw Error('This file exceeds 30 MB. Upload a figure image or a smaller PDF.');
 await clearDocument();task('Reading your file locally…');const data=await file.arrayBuffer(),signature=new TextDecoder().decode(data.slice(0,1024)),isPDF=signature.includes('%PDF-');source={name:file.name||'Pasted screenshot.png',type:isPDF?'pdf':'image',sha256:await digest(data)};
 if(isPDF){
   task('Opening PDF and checking the first six pages for a colored figure…');
   pdfModule=pdfModule||await import('./pdfjs/build/pdf.mjs');pdfModule.GlobalWorkerOptions.workerSrc=new URL('assets/pdfjs/build/pdf.worker.mjs',document.baseURI).href;
   const loading=pdfModule.getDocument({data:new Uint8Array(data),cMapUrl:new URL('assets/pdfjs/cmaps/',document.baseURI).href,cMapPacked:true,standardFontDataUrl:new URL('assets/pdfjs/standard_fonts/',document.baseURI).href,wasmUrl:new URL('assets/pdfjs/wasm/',document.baseURI).href,isEvalSupported:false,enableScripting:false,useSystemFonts:false});
   pdfTask=loading;loading.onPassword=()=>{loading.destroy();task('This PDF is password protected. Upload an unlocked copy or a screenshot.',true)};
   pdf=await loading.promise;$('pdf-controls').hidden=false;$('pdf-total').textContent=`of ${pdf.numPages}`;$('pdf-page').max=pdf.numPages;
   let bestPage=1,bestScore=-1;const probe=document.createElement('canvas');
   for(let i=1;i<=Math.min(6,pdf.numPages);i++){
    task(`Finding a colored figure · page ${i} of ${Math.min(6,pdf.numPages)}…`);await showPDFPage(i,probe);
    try{let r=await runExtraction(samplePixels(probe)),score=r.retained_pixels;if(score>bestScore){bestScore=score;bestPage=i}}catch(error){if(!error.message.startsWith('Fewer')&&!error.message.startsWith('Only one'))throw error}
   }
   probe.width=probe.height=1;await showPDFPage(bestPage);
 }else{
   if(!['image/png','image/jpeg','image/webp'].includes(file.type)&&!(/\.(png|jpe?g|webp)$/i.test(file.name)))throw Error('Use a PDF, PNG, JPG or WebP file.');
   const bitmap=await createImageBitmap(new Blob([data],{type:file.type||'image/png'}));
   if(bitmap.width*bitmap.height>64000000||Math.max(bitmap.width,bitmap.height)>16000){bitmap.close();throw Error('Image dimensions are too large. Export a figure below 64 megapixels.');}
   const scale=Math.min(1,2400/Math.max(bitmap.width,bitmap.height));source.original_width=bitmap.width;source.original_height=bitmap.height;sourceCanvas.width=Math.round(bitmap.width*scale);sourceCanvas.height=Math.round(bitmap.height*scale);
   sourceCtx.fillStyle='#FFFFFF';sourceCtx.fillRect(0,0,sourceCanvas.width,sourceCanvas.height);sourceCtx.imageSmoothingEnabled=false;sourceCtx.drawImage(bitmap,0,0,sourceCanvas.width,sourceCanvas.height);bitmap.close();revealSource();
 }
 await extractCurrent();
 }catch(error){task(error.message||'The file could not be opened. Try an image or an unlocked PDF.',true)}finally{lock(false)}
}
$('file-input').onchange=e=>{const f=e.target.files[0];if(f)loadFile(f)};
$('dropzone').onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();if(!busy)$('file-input').click()}};
for(let name of ['dragenter','dragover'])$('dropzone').addEventListener(name,e=>{e.preventDefault();$('dropzone').classList.add('drag-over')});
$('dropzone').addEventListener('dragleave',()=>$('dropzone').classList.remove('drag-over'));
$('dropzone').addEventListener('drop',e=>{e.preventDefault();$('dropzone').classList.remove('drag-over');if(e.dataTransfer.files[0])loadFile(e.dataTransfer.files[0])});
window.addEventListener('dragover',e=>e.preventDefault());window.addEventListener('drop',e=>e.preventDefault());
window.addEventListener('paste',e=>{const item=[...(e.clipboardData?.items||[])].find(x=>x.type.startsWith('image/'));if(item){e.preventDefault();const blob=item.getAsFile();loadFile(new File([blob],'Pasted screenshot.png',{type:blob.type}))}});
$('extract').onclick=async()=>{if(busy)return;lock(true);try{await extractCurrent()}catch(e){task(e.message,true)}finally{lock(false)}};
$('show-page').onclick=async()=>{if(busy||!pdf)return;lock(true);try{const n=+ $('pdf-page').value;if(!Number.isInteger(n)||n<1||n>pdf.numPages)throw Error(`Choose a page from 1 to ${pdf.numPages}.`);resetResult();task('Rendering the selected PDF page…');await showPDFPage(n);await extractCurrent()}catch(e){task(e.message,true)}finally{lock(false)}};
$('pdf-page').onkeydown=e=>{if(e.key==='Enter')$('show-page').click()};
$('clear-source').onclick=async()=>{if(busy)return;lock(true);try{await clearDocument();task('Ready when you are.')}finally{lock(false)}};
$('try-sample').onclick=async()=>{
 if(busy)return;lock(true);try{await clearDocument();source={name:'Original sample figure',type:'original sample',demo:true};sourceCanvas.width=1200;sourceCanvas.height=670;sourceCtx.fillStyle='#FFFFFF';sourceCtx.fillRect(0,0,1200,670);
 sourceCtx.fillStyle='#333333';sourceCtx.font='27px Arial';sourceCtx.fillText('Mineral & molecular colors',50,55);sourceCtx.font='15px Arial';sourceCtx.fillStyle='#666666';sourceCtx.fillText('Original demonstration · illustrative data',50,85);
 sourceCtx.strokeStyle='#DCE3EC';sourceCtx.lineWidth=1;for(let y=160;y<=460;y+=60){sourceCtx.beginPath();sourceCtx.moveTo(75,y);sourceCtx.lineTo(1130,y);sourceCtx.stroke()}
 for(let [i,c]of window.PALETTE_PAYLOAD.palette.main.entries()){sourceCtx.strokeStyle=c.hex;sourceCtx.lineWidth=7;sourceCtx.beginPath();for(let x=0;x<32;x++){let X=85+x*32,Y=435-i*30-44*Math.sin(x*.19+i*.5)-x*4;x?sourceCtx.lineTo(X,Y):sourceCtx.moveTo(X,Y)}sourceCtx.stroke();sourceCtx.fillStyle=c.hex;sourceCtx.fillRect(75+i*178,525,160,65);sourceCtx.fillStyle='#333333';sourceCtx.font='19px monospace';sourceCtx.fillText(c.hex,75+i*178,620)}
 revealSource();await extractCurrent();
 }catch(e){task(e.message,true)}finally{lock(false)}
};
$('use-manual').onclick=async()=>{if(busy)return;const colors=$('manual-colors').value.trim().split(/[\s,;]+/).filter(Boolean).map(x=>(x.startsWith('#')?x:'#'+x).toUpperCase());if(colors.length<2||colors.length>8||colors.some(x=>!/^#[0-9A-F]{6}$/.test(x))||new Set(colors).size!==colors.length){task('Enter 2–8 distinct six-digit HEX colors, such as #28669B #DB7853.',true);return}lock(true);try{await clearDocument();applyPalette(colors,{basis:'manual'},'My scientific palette');task('Your manual palette and all derived gradients are ready below.')}finally{lock(false)}};
// Portable exports share the same live palette as the editable workbench.
function colorsCSV(){let lines=['role,index,hex,r,g,b'];palette.main.forEach((c,i)=>lines.push(['main',i+1,c.hex,...rgb(c.hex)].join(',')));for(let g of palette.gradients)g.colors.forEach((c,i)=>lines.push([g.id,i,c,...rgb(c)].join(',')));return lines.join('\r\n')+'\r\n'}
async function cardPNG(){const blob=new Blob([cardSVG()],{type:'image/svg+xml'}),url=URL.createObjectURL(blob);try{const im=new Image();im.src=url;await im.decode();const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;c.getContext('2d').drawImage(im,0,0);return await new Promise((resolve,reject)=>c.toBlob(b=>b?resolve(b):reject(Error('PNG export failed.')),'image/png'))}finally{URL.revokeObjectURL(url)}}
const baseKit=kit;
kit=async()=>{let out=await baseKit(),png=await cardPNG();out['color-card.png']=new Uint8Array(await png.arrayBuffer());out['colors.csv']=colorsCSV();out['HOW-TO-USE.txt']+='\nColor card: PNG for slides; SVG for vector editing. colors.csv contains the main colors and all 257 gradient samples.\nPrivacy: files are processed in the browser and are not uploaded.\nColor extraction identifies rendered pixels, not author-specified vector color values. Gradients are derived.\nOffice themes have six accents. Additional main colors remain editable in the PPTX.\nJASC-PAL files contain colors only; set levels and diverging center separately in Origin.\n';return out};
$('download-png').onclick=async()=>{try{download('color-card.png',await cardPNG())}catch(e){status('Export failed: '+e.message)}};
$('download-svg').onclick=()=>download('color-card.svg',cardSVG(),'image/svg+xml');$('download-csv').onclick=()=>download('colors.csv',colorsCSV(),'text/csv');
const resetButton=$('reset').onclick;$('reset').onclick=()=>{resetButton();$('basis').textContent=`Main colors: ${palette.provenance.basis} · Gradients: derived · sRGB`};
// Edit events call the shared render; its provenance is always displayed alongside the palette.
