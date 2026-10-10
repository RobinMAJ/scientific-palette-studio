import {test} from 'node:test';
import assert from 'node:assert/strict';
import {extractPixels} from '../dist/assets/extract.mjs';
const colors=['#28669B','#DB7853','#439B91','#9274AA','#D1AA45','#BA637F'];
const rgb=c=>[1,3,5].map(i=>parseInt(c.slice(i,i+2),16));
function pixels(cs,n=400){let out=new Uint8ClampedArray(cs.length*n*4);cs.forEach((c,i)=>{for(let k=0;k<n;k++)out.set([...rgb(c),255],4*(i*n+k))});return out}
test('six solid figure colors are source-exact and deterministic',()=>{let p=pixels([...colors,'#FFFFFF','#000000','#777777']),a=extractPixels(p,6);assert.deepEqual(new Set(a.colors),new Set(colors));assert.deepEqual(a,extractPixels(p,6));assert.equal(a.returned_colors,6)});
test('no extra hues invented for a two-color source',()=>{const a=extractPixels(pixels(colors.slice(0,2)),8);assert.equal(a.returned_colors,2);assert.deepEqual(new Set(a.colors),new Set(colors.slice(0,2)))});
test('default ignores neutral pixels; neutral inclusion is explicit',()=>{assert.throws(()=>extractPixels(pixels(['#777777','#999999']),2),/Fewer/);assert.equal(extractPixels(pixels(['#777777','#999999']),2,true).colors.length,2)});
test('white and black exclusion does not suppress a thin colored line',()=>{let p=pixels(['#FFFFFF'],10000);let q=pixels(colors.slice(0,2),100);let r=new Uint8ClampedArray(p.length+q.length);r.set(p);r.set(q,p.length);assert.deepEqual(new Set(extractPixels(r,2).colors),new Set(colors.slice(0,2)))});
test('opaque representatives survive lower-frequency antialias pixels',()=>{let p=pixels(colors,1000),q=pixels(['#8CAA C6'.replace(' ',''),'#EDBCAA','#A1CDC8'],40),r=new Uint8ClampedArray(p.length+q.length);r.set(p);r.set(q,p.length);assert.deepEqual(new Set(extractPixels(r,6).colors),new Set(colors))});
test('validation and sample bound',()=>{assert.throws(()=>extractPixels(pixels(colors),9),/2–8/);assert.throws(()=>extractPixels(pixels(['#FFFFFF']),6),/Fewer/);let a=extractPixels(pixels(colors,30000),6);assert.ok(a.sampled_pixels<=160000)});
