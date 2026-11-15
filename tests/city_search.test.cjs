const {test}=require('node:test');
const assert=require('node:assert/strict');
const {ukKind,createLookup}=require('../skills/city-wuxing-map/assets/search.js');
const reply=(data,status=200)=>({ok:status===200,status,json:async()=>data});

test('recognizes UK formats without treating foreign postal formats as UK codes',()=>{
 assert.equal(ukKind('sw1a 1aa'),'postcode');assert.equal(ukKind('EC1A1BB'),'postcode');
 assert.equal(ukKind('SW1A'),'outcode');assert.equal(ukKind('sw1'),'outcode');
 for(const value of ['10013','75001','101-0021','皇后大道','H2X 1Y4'])assert.equal(ukKind(value),null);
});
test('UK postcode lookup normalizes whitespace and caches repeated queries',async()=>{
 const urls=[];const lookup=createLookup(async url=>{urls.push(url);return reply({result:{postcode:'SW1A 1AA',longitude:-.141,latitude:51.501}})});
 const a=await lookup(' sw1a 1aa ',{country_code:'gb'});await lookup('SW1A1AA',{country_code:'gb'});
 assert.equal(urls.length,1);assert.match(urls[0],/postcodes\/SW1A1AA$/);assert.deepEqual(a[0].position,[-.141,51.501]);assert.equal(a[0].approximate,false);
});
test('district centroid is explicitly approximate; split district offers subdivisions without matching SW10',async()=>{
 const centroid=createLookup(async()=>reply({result:{outcode:'SW1A',longitude:-.13,latitude:51.5}}));
 assert.equal((await centroid('SW1A',{country_code:'gb'}))[0].approximate,true);
 const urls=[];const lookup=createLookup(async url=>{
  urls.push(url);
  if(urls.length===1)return reply({},404);
  if(urls.length===2)return reply({result:{outcode:'SW1A',longitude:-.13,latitude:51.5}});
  return reply({result:[{outcode:'SW1P',longitude:-.14,latitude:51.5},{outcode:'SW10',longitude:-.18,latitude:51.49}]});
 });
 const results=await lookup('SW1',{country_code:'gb'});assert.equal(results.length,2);assert.match(urls[2],/nearest/);assert.match(results[0].label,/SW1A/);assert.ok(results.every(r=>r.approximate));assert.ok(results.every(r=>!r.label.includes('SW10')));
});
test('other countries use Unicode address/postal search, bounding box and country validation',async()=>{
 let url;const lookup=createLookup(async u=>{url=new URL(u);return reply({features:[{geometry:{type:'Point',coordinates:[2.35,48.85]},properties:{postcode:'75001',countrycode:'FR',name:'巴黎'}},{geometry:{type:'Point',coordinates:[0,0]},properties:{countrycode:'US'}},{geometry:{type:'Point',coordinates:[null,48]},properties:{}}]})});
 const values=await lookup('75001 巴黎',{country_code:'fr',bbox:[2,48,3,49],photon_url:'https://geo.example/api/'});
 assert.equal(url.hostname,'geo.example');assert.equal(url.searchParams.get('q'),'75001 巴黎');assert.equal(url.searchParams.get('bbox'),'2,48,3,49');assert.equal(values.length,1);assert.match(values[0].label,/巴黎/);
});
test('service failures and aborts are not silently converted to a location',async()=>{
 const fail=createLookup(async()=>reply({},429));await assert.rejects(fail('10013',{country_code:'us'}),/429/);
 const controller=new AbortController();controller.abort();let called=false;
 const lookup=createLookup(async()=>{called=true;return reply({})});await assert.rejects(lookup('10013',{},controller.signal),{name:'AbortError'});assert.equal(called,false);
});
