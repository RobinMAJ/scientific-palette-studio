// Source-color representatives in Oklab: deterministic, bounded, never synthesize extra hues.
const lin=v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4;
function labRGB([R,G,B]){const [r,g,b]=[R,G,B].map(v=>lin(v/255)),l=Math.cbrt(.4122214708*r+.5363325363*g+.0514459929*b),m=Math.cbrt(.2119034982*r+.6806995451*g+.1073969566*b),s=Math.cbrt(.0883024619*r+.2817188376*g+.6299787005*b);return [.2104542553*l+.793617785*m-.0040720468*s,1.9779984951*l-2.428592205*m+.4505937099*s,.0259040371*l+.7827717662*m-.808675766*s]}
const dist=(a,b)=>a.reduce((v,x,i)=>v+(x-b[i])**2,0);
const hex=a=>'#'+a.map(x=>x.toString(16).padStart(2,'0')).join('').toUpperCase();
export function extractPixels(pixels,count=6,includeNeutrals=false){
 if(!(pixels instanceof Uint8ClampedArray)||pixels.length%4)throw Error('Invalid pixel buffer.');
 if(!Number.isInteger(count)||count<2||count>8)throw Error('Choose 2–8 main colors.');
 const histogram=new Map();let sampled=0;
 const stride=Math.max(1,Math.ceil(pixels.length/4/160000));
 for(let i=0;i<pixels.length;i+=4*stride){const a=pixels[i+3]/255; if(a<.05)continue;const c=[0,1,2].map(k=>Math.round(pixels[i+k]*a+255*(1-a))),key=c[0]*65536+c[1]*256+c[2];histogram.set(key,(histogram.get(key)||0)+1);sampled++}
 const bins=new Map();let retained=0;
 for(let [key,weight]of histogram){let c=[key>>>16,(key>>>8)&255,key&255],lab=labRGB(c),chroma=Math.hypot(lab[1],lab[2]);if(lab[0]<.12||lab[0]>.97||(!includeNeutrals&&chroma<.025))continue;retained+=weight;let bin=(c[0]>>3)*1024+(c[1]>>3)*32+(c[2]>>3),p=bins.get(bin);if(!p)bins.set(bin,{c,lab,weight,representative:weight,key});else{p.weight+=weight;if(weight>p.representative||(weight===p.representative&&key<p.key)){p.c=c;p.lab=lab;p.representative=weight;p.key=key}}}
 const points=[...bins.values()].sort((a,b)=>b.weight-a.weight||a.key-b.key);
 if(points.length<2)throw Error('Fewer than two usable colors found. Select a colored figure, include neutrals, or enter your own HEX colors.');
 let centers=[points[0].lab];
 while(centers.length<count){let best=null,score=-1;for(let p of points){let d=Math.min(...centers.map(c=>dist(p.lab,c))),s=d*Math.sqrt(p.weight);if(d>=.035**2&&s>score){score=s;best=p}}if(!best)break;centers.push(best.lab)}
 let labels=[];
 for(let iteration=0;iteration<16;iteration++){let sums=centers.map(()=>[0,0,0]),weights=centers.map(()=>0);labels=points.map(p=>{let best=0,bestD=Infinity;centers.forEach((c,i)=>{let d=dist(p.lab,c);if(d<bestD){bestD=d;best=i}});sums[best]=sums[best].map((v,i)=>v+p.lab[i]*p.weight);weights[best]+=p.weight;return best});centers=centers.map((c,i)=>weights[i]?sums[i].map(v=>v/weights[i]):c)}
 const groups=centers.map((center,i)=>{let choices=points.filter((_,j)=>labels[j]===i);if(!choices.length)return null;choices.sort((a,b)=>b.weight-a.weight||dist(a.lab,center)-dist(b.lab,center)||a.key-b.key);return {hex:hex(choices[0].c),weight:choices.reduce((s,p)=>s+p.weight,0)}}).filter(Boolean).sort((a,b)=>b.weight-a.weight||a.hex.localeCompare(b.hex));
 const unique=[...new Set(groups.map(x=>x.hex))];if(unique.length<2)throw Error('Only one distinct color remains. Include neutrals or choose a different area.');
 return {colors:unique,sampled_pixels:sampled,retained_pixels:retained,coverage:sampled?retained/sampled:0,requested_colors:count,returned_colors:unique.length,method:'Weighted Oklab clustering with observed source-color representatives; sRGB rendering; white, near-black and optionally neutral pixels excluded.'};
}
