/* Postal/address lookup independent of map rendering. Public services are best-effort. */
(function(root){
'use strict';
function ukKind(query){
 const q=query.toUpperCase().replace(/\s+/g,'');
 if(/^(GIR0AA|[A-Z]{1,2}\d[A-Z\d]?\d[A-Z]{2})$/.test(q))return 'postcode';
 if(/^[A-Z]{1,2}\d[A-Z\d]?$/.test(q))return 'outcode';
 return null;
}
function point(lon,lat,label,source,approximate=false){
 if(!Number.isFinite(lon)||!Number.isFinite(lat)||Math.abs(lon)>180||Math.abs(lat)>85.05112878)return null;
 return {position:[lon,lat],label,source,approximate};
}
function createLookup(fetcher=fetch){
 const cache=new Map();let lastRequest=0;
 async function read(url,signal){
  if(cache.has(url))return cache.get(url);
  const wait=Math.max(0,1100-(Date.now()-lastRequest));
  if(wait)await new Promise(resolve=>setTimeout(resolve,wait));
  signal?.throwIfAborted();lastRequest=Date.now();
  const response=await fetcher(url,{signal,credentials:'omit'});
  if(response.status===404)return null;
  if(!response.ok)throw new Error('定位服务暂时不可用（'+response.status+'），请稍后重试或输入坐标。');
  const value=await response.json();cache.set(url,value);return value;
 }
 return async function lookup(query,options={},signal){
  const q=query.trim();if(!q)return [];
  if(options.country_code==='gb'&&ukKind(q)){
   const compact=q.toUpperCase().replace(/\s+/g,''),kind=ukKind(q);
   const result=await read('https://api.postcodes.io/'+(kind==='postcode'?'postcodes/':'outcodes/')+encodeURIComponent(compact),signal);
   if(result?.result){const p=result.result;return [point(p.longitude,p.latitude,p.postcode||p.outcode,'Postcodes.io',kind==='outcode')].filter(Boolean);}
   if(kind==='postcode')return [];
   // Split districts (SW1 -> SW1A, SW1E, ...) must not prefix-match SW10.
   // Find the A subdivision and its nearby official outward-code centres,
   // then retain only subdivisions of the exact requested district.
   const anchor=await read('https://api.postcodes.io/outcodes/'+encodeURIComponent(compact+'A'),signal);
   if(!anchor?.result)return [];
   const nearby=await read('https://api.postcodes.io/outcodes/'+encodeURIComponent(compact+'A')+'/nearest?limit=100&radius=25000',signal);
   const unique=new Map([anchor.result,...(nearby?.result||[])].map(p=>[p.outcode,p]));
   return [...unique.values()].filter(p=>p.outcode.startsWith(compact)&&/^[A-Z]$/.test(p.outcode.slice(compact.length))).map(p=>point(p.longitude,p.latitude,p.outcode+' · '+compact+(options.lang==='en'?' sub-district':'细分邮区'),'Postcodes.io',true)).filter(Boolean);
  }
  const url=new URL(options.photon_url||'https://photon.komoot.io/api/');
  url.searchParams.set('q',q);url.searchParams.set('limit','8');
  if(options.lang==='en')url.searchParams.set('lang','en');   // Photon 的英文地名；中文页沿用默认（当地名称）
  if(options.bbox)url.searchParams.set('bbox',options.bbox.join(','));
  const result=await read(url.href,signal);
  return (result?.features||[]).filter(f=>!options.country_code||!f.properties?.countrycode||f.properties.countrycode.toLowerCase()===options.country_code).map(f=>{
   const p=f.properties||{},c=f.geometry?.coordinates;
   if(f.geometry?.type!=='Point'||!Array.isArray(c))return null;
   const label=[p.name,[p.housenumber,p.street].filter(Boolean).join(' '),p.postcode,p.city||p.district,p.country].filter(Boolean);
   return point(c[0],c[1],[...new Set(label)].join(' · '),'Photon / © OpenStreetMap contributors',!p.housenumber);
  }).filter(Boolean);
 };
}
const api={ukKind,createLookup};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.CitySearch=api;
})(globalThis);
