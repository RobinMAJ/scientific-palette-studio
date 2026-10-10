'use strict';
// Presentation only. Every panel reads the same live palette and export engine.
const workspaceTabs=[...document.querySelectorAll('[role="tab"][data-panel]')];
function openWorkspacePanel(name,focus=false){
  const target=workspaceTabs.find(tab=>tab.dataset.panel===name);
  if(!target)return;
  for(const tab of workspaceTabs){
    const active=tab===target;
    tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;
    document.getElementById(tab.getAttribute('aria-controls')).hidden=!active;
  }
  if(focus)target.focus();
}
for(const tab of workspaceTabs){
  tab.addEventListener('click',()=>openWorkspacePanel(tab.dataset.panel));
  tab.addEventListener('keydown',event=>{
    let index=workspaceTabs.indexOf(tab),next=null;
    if(event.key==='ArrowRight')next=(index+1)%workspaceTabs.length;
    if(event.key==='ArrowLeft')next=(index-1+workspaceTabs.length)%workspaceTabs.length;
    if(event.key==='Home')next=0;
    if(event.key==='End')next=workspaceTabs.length-1;
    if(next!==null){event.preventDefault();openWorkspacePanel(workspaceTabs[next].dataset.panel,true)}
  });
}
for(const button of document.querySelectorAll('[data-open-panel]'))button.addEventListener('click',()=>openWorkspacePanel(button.dataset.openPanel,true));
for(const id of ['sequential','diverging'])document.getElementById(id).addEventListener('keydown',event=>{
  if(event.key==='Enter'||event.key===' '){event.preventDefault();event.currentTarget.click()}
});
function updateWorkspaceSummary(){
  const visible=!document.getElementById('results').hidden;
  document.getElementById('view-palette').hidden=!visible;
  if(visible){
    const count=document.querySelectorAll('#colors .color').length;
    document.getElementById('palette-summary').textContent=`${count} main colors · ${count+2} gradients`;
    const checks=palette.audit.warnings.length;
    document.getElementById('audit-summary').textContent=checks?`${checks} review ${checks===1?'note':'notes'}`:'No heuristic warnings';
  }
}
new MutationObserver(updateWorkspaceSummary).observe(document.getElementById('results'),{attributes:true,attributeFilter:['hidden']});
new MutationObserver(updateWorkspaceSummary).observe(document.getElementById('colors'),{childList:true});
// A new source starts at its main colors; editing keeps the selected panel.
new MutationObserver(()=>{
  if(!document.getElementById('results').hidden)openWorkspacePanel('palette');
}).observe(document.getElementById('results'),{attributes:true,attributeFilter:['hidden']});
updateWorkspaceSummary();
