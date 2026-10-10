// Maintainer-only: author the reusable, original editable template with Artifact Tool.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const build=path.join(root,'.build');
await fs.mkdir(build,{recursive:true});
const colors=['#28669B','#DB7853','#439B91','#9274AA','#D1AA45','#BA637F','#697EA4','#768D52'];
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
presentation.theme.defaultFont='Arial';
presentation.theme.colorScheme={name:'Scientific Palette Studio',themeColors:{
  accent1:colors[0],accent2:colors[1],accent3:colors[2],accent4:colors[3],accent5:colors[4],accent6:colors[5],
  bg1:'#FFFFFF',bg2:'#F1F4F7',tx1:'#182533',tx2:'#445465',dk1:'#182533',dk2:'#445465',lt1:'#FFFFFF',lt2:'#F1F4F7',
  hlink:colors[0],folHlink:colors[5]}};
function txt(s,name,text,x,y,w,h,size=26,bold=false,color='#182533'){
  const sh=s.shapes.add({name,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=text;sh.text.style={fontFamily:'Arial',fontSize:size,bold,color};return sh;
}
function rect(s,name,x,y,w,h,fill){return s.shapes.add({name,geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:'none',width:0}});}
function slide(title,subtitle,titleName='TITLE'){const s=presentation.slides.add();s.background.fill='#FFFFFF';
  txt(s,titleName,title,64,42,1152,65,44,true);txt(s,'SUBTITLE',subtitle,64,108,1152,45,25,false,'#445465');return s;}
const s1=slide('Scientific Palette Studio','Editable swatches / exact sRGB values','PALETTE_TITLE');
for(let i=0;i<8;i++){
 const x=64+(i%4)*287,y=180+Math.floor(i/4)*220,c=colors[i];
 rect(s1,`MAIN-${i}`,x,y,267,110,c);
 txt(s1,`HEX-${i}`,`${String(i+1).padStart(2,'0')}  ${c}`,x,y+122,267,40,28,true);
 const rgb=c.match(/[0-9a-f]{2}/gi).map(v=>parseInt(v,16));
 txt(s1,`RGB-${i}`,`RGB ${rgb.join(' / ')}`,x,y+162,267,40,24,false,'#445465');
}
txt(s1,'PALETTE_BASIS','8 main colors · original template · sRGB',64,644,1152,40,23,false,'#445465');
const s2=slide('Shades, tints and tonal gradients','Light → main color at 50% → dark. Copy any gradient or discrete swatch.');
for(let i=0;i<8;i++){
 const y=168+i*57;
 txt(s2,`TONE_LABEL-${i}`,`${String(i+1).padStart(2,'0')}  ${colors[i]}`,64,y,214,40,25,true);
 rect(s2,`TONAL-${i}`,290,y,610,34,{type:'gradient',gradientKind:'linear',angleDeg:0,
  stops:[{offset:0,color:'#FFFFFF'},{offset:50000,color:colors[i]},{offset:100000,color:'#182533'}]});
 for(let j=0;j<7;j++)rect(s2,`SHADE-${i}-${j}`,934+j*36,y,30,34,colors[i]);
}
txt(s2,'FOOTER','Gradients are derived from the main colors. The seven samples are reusable fills.',64,646,1152,40,23,false,'#445465');
const s3=slide('Continuous color scales','Sequential for ordered values / diverging for values around a meaningful center');
txt(s3,'SEQ_LABEL','Multihue sequential',64,194,1152,40,30,true);
rect(s3,'SEQUENTIAL',64,247,1152,80,{type:'gradient',gradientKind:'linear',angleDeg:0,stops:[{offset:0,color:'#F1F4F7'},{offset:100000,color:colors[0]}]});
txt(s3,'SEQ_DIRECTION','Light / low',64,339,350,40,24);txt(s3,'SEQ_HIGH','Dark / high',1020,339,196,40,24);
txt(s3,'DIV_LABEL','Diverging with a neutral center',64,419,1152,40,30,true);
rect(s3,'DIVERGING',64,472,1152,80,{type:'gradient',gradientKind:'linear',angleDeg:0,stops:[{offset:0,color:colors[0]},{offset:50000,color:'#F5F5F5'},{offset:100000,color:colors[1]}]});
txt(s3,'DIV_LEFT','Low',64,564,200,40,24);txt(s3,'DIV_CENTER','Center',590,564,200,40,24);txt(s3,'DIV_RIGHT','High',1130,564,86,40,24);
txt(s3,'FOOTER','Set data limits and the center in your plotting software; this file supplies colors.',64,644,1152,40,23,false,'#445465');
const s4=slide('Reuse in PowerPoint and Origin','The exported files share the same palette and RGB values.');
const lines=[
 ['PowerPoint theme','Design → Themes → Browse for Themes → palette.thmx'],
 ['Editable gradient fills','Copy a swatch or gradient shape; use Format Painter to transfer its fill.'],
 ['Origin color list','Tools → Color Manager → Import from Files → main-colors.pal'],
 ['Origin continuous scales','Import a tonal, sequential or diverging .pal file; then choose it for the colormap.'],
 ['More than six main colors','PowerPoint has six accent slots. Extra colors stay in the swatch deck.']
];
for(let i=0;i<lines.length;i++){
 txt(s4,`USAGE_TITLE-${i}`,lines[i][0],64,186+i*87,1152,38,28,true);
 txt(s4,`USAGE_BODY-${i}`,lines[i][1],64,224+i*87,1152,40,24,false,'#445465');
}
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidate);
const skillDir=process.env.PALETTE_PRESENTATIONS_SKILL;
if(!skillDir)throw Error('Set PALETTE_PRESENTATIONS_SKILL to the installed presentations skill.');
const {finalizePresentation}=await import(pathToFileURL(path.join(skillDir,'container_tools/artifact_tool_utils.mjs')).href);
await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(root,'assets/palette-template.pptx'),
 pythonExecutable:process.env.PALETTE_PYTHON,integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit'],
 fontPolicy:{basis:'design',families:['Arial']},explicitTotalSlideCount:4,verifyArtifactToolImport:true,
 receiptPath:path.join(build,'template-validation.json')});
for(const [i,s] of presentation.slides.items.entries()){
 const png=await presentation.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(build,`template-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
console.log('Original native template created.');
