import {extractPixels} from './extract.mjs';
self.onmessage=e=>{const {id,pixels,count,includeNeutrals}=e.data;try{self.postMessage({id,result:extractPixels(new Uint8ClampedArray(pixels),count,includeNeutrals)})}catch(error){self.postMessage({id,error:error.message})}};
