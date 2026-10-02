module.exports = function run(B, foreign, nodeBuffer) {
  const cases = [];
  const assert = (condition, name) => { if (!condition) throw Error(name); };
  const same = (a,b) => a.length === b.length && a.every((x,i) => x === b[i]);
  const bytes = a => Array.from(new Uint8Array(a.buffer,a.byteOffset,a.byteLength));
  const reject = (name, fn) => {
    try { fn(); } catch (error) {
      assert(error.cause?.MEL_EXN_ID === 'Invalid_argument' || error.MEL_EXN_ID === 'Invalid_argument' || String(error).includes('Invalid_argument'), name+': wrong exception '+String(error));
      cases.push(name); return;
    }
    throw Error(name+': accepted invalid input');
  };
  const constructors = [Float32Array,Float64Array,Int8Array,Uint8Array,Int16Array,Uint16Array,Int32Array,Int32Array,Int32Array,Int32Array,Float32Array,Float64Array,Uint8Array,Uint16Array];
  const names = ['float32','float64','int8_signed','int8_unsigned','int16_signed','int16_unsigned','int32','int64','int','nativeint','complex32','complex64','char','float16'];
  for (let kind=0;kind<names.length;kind++) {
    const selected=B[names[kind]] ?? B['$$'+names[kind]];
    if (selected === undefined) { assert(kind===13,'missing required kind'); continue; }
    const lanes = [7,10,11].includes(kind) ? 2 : 1;
    const source = new constructors[kind](2*lanes);
    for (let i=0;i<source.length;i++) source[i] = i*11+1;
    const array = B.Interop.import_copy(selected, B.c_layout, [2], source);
    assert(same(bytes(source),bytes(B.Interop.export_copy(array))), names[kind]+': copy bits');
    const shared = B.Interop.import_shared(selected, B.fortran_layout, [2], source);
    assert(same(bytes(source),bytes(B.Interop.export_shared(shared))), names[kind]+': shared bits');
    cases.push(names[kind]+'-roundtrip');
  }
  const original = new Uint8Array([1,2,3]);
  const copy = B.Interop.import_copy(B.int8_unsigned,B.c_layout,[3],original);
  original[0]=9;
  assert(B.Genarray.get(copy,[0])===1,'import copy ownership');
  const exportedCopy=B.Interop.export_copy(copy);
  exportedCopy[1]=8;
  assert(B.Genarray.get(copy,[1])===2,'export copy ownership');
  cases.push('copy-ownership');
  const backing = new Float64Array([1,2,3,4]);
  const input=backing.subarray(1,3);
  const dimensions=[2];
  const shared=B.Interop.import_shared(B.float64,B.c_layout,dimensions,input);
  dimensions[0]=99;
  const returnedDimensions=B.Genarray.dims(shared); returnedDimensions[0]=88;
  assert(B.Genarray.nth_dim(shared,0)===2,'owned metadata');
  B.Genarray.set(shared,[0],11);
  input[1]=22;
  assert(backing[1]===11 && B.Genarray.get(shared,[1])===22,'shared mutations');
  const exported=B.Interop.export_shared(shared);
  assert(exported.byteOffset===8 && exported.length===2 && exported.buffer===backing.buffer,'shared exact extent');
  exported[0]=33;
  assert(input[0]===33,'shared export mutation');
  cases.push('offset-length-alias-metadata');
  const remote=foreign('new Uint8Array([7,8,9])');
  const remoteArray=B.Interop.import_shared(B.int8_unsigned,B.c_layout,[3],remote);
  B.Genarray.set(remoteArray,[1],42);
  assert(remote[1]===42,'cross-realm shared view');
  cases.push('cross-realm');
  if (nodeBuffer) {
    const buffer=nodeBuffer.from([5,6,7,8]).subarray(1,3);
    const array=B.Interop.import_shared(B.int8_unsigned,B.c_layout,[2],buffer);
    B.Genarray.set(array,[0],21);
    assert(buffer[0]===21,'Node Buffer alias');
    cases.push('node-buffer');
  }
  reject('plain-object',()=>B.Interop.import_shared(B.float64,B.c_layout,[1],{0:1,length:1,buffer:new ArrayBuffer(8)}));
  reject('spoofed-tag',()=>B.Interop.import_copy(B.float64,B.c_layout,[1],{[Symbol.toStringTag]:'Float64Array',length:1}));
  reject('spoofed-prototype',()=>B.Interop.import_shared(B.float64,B.c_layout,[1],Object.create(Float64Array.prototype)));
  reject('proxy',()=>B.Interop.import_shared(B.float64,B.c_layout,[1],new Proxy(new Float64Array(1),{})));
  reject('data-view',()=>B.Interop.import_shared(B.float64,B.c_layout,[1],new DataView(new ArrayBuffer(8))));
  reject('wrong-kind',()=>B.Interop.import_shared(B.float64,B.c_layout,[1],new Float32Array(1)));
  reject('wrong-length',()=>B.Interop.import_shared(B.float64,B.c_layout,[2],new Float64Array(1)));
  reject('wrong-alignment',()=>B.Interop.import_shared(B.int64,B.c_layout,[1],new Int32Array(new ArrayBuffer(16),4,2)));
  reject('invalid-dimension',()=>B.Interop.import_shared(B.float64,B.c_layout,[1.5],new Float64Array(1)));
  assert(typeof SharedArrayBuffer==='function','SharedArrayBuffer rejection fixture unavailable');
  reject('shared-buffer',()=>B.Interop.import_shared(B.float64,B.c_layout,[1],new Float64Array(new SharedArrayBuffer(8))));
  assert(new ArrayBuffer(8,{maxByteLength:16}).resizable,'resizable rejection fixture unavailable');
  reject('resizable-buffer',()=>B.Interop.import_shared(B.float64,B.c_layout,[1],new Float64Array(new ArrayBuffer(8,{maxByteLength:16}))));
  const detachable=new Float64Array([1,2]);
  const imported=B.Interop.import_shared(B.float64,B.c_layout,[2],detachable);
  structuredClone(detachable.buffer,{transfer:[detachable.buffer]});
  reject('detached-before-import',()=>B.Interop.import_shared(B.float64,B.c_layout,[0],detachable));
  reject('detached-get',()=>B.Genarray.get(imported,[0]));
  reject('detached-set',()=>B.Genarray.set(imported,[0],1));
  reject('detached-fill',()=>B.Genarray.fill(imported,1));
  reject('detached-blit',()=>B.Genarray.blit(imported,copy));
  reject('detached-reshape',()=>B.reshape(imported,[2]));
  reject('detached-export',()=>B.Interop.export_copy(imported));
  const owned=B.Genarray.create(B.float64,B.c_layout,[4]); B.Genarray.fill(owned,0);
  const oldView=B.Genarray.sub_left(owned,1,2);
  const exposed=B.Interop.export_shared(oldView);
  assert(exposed.byteOffset===8 && exposed.length===2,'owned subview export extent');
  structuredClone(exposed.buffer,{transfer:[exposed.buffer]});
  reject('detached-earlier-owner',()=>B.Genarray.get(owned,[0]));
  reject('detached-earlier-view',()=>B.Genarray.get(oldView,[0]));
  const emptyData=new Uint8Array(0);
  const empty=B.Interop.import_shared(B.int8_unsigned,B.c_layout,[0],emptyData);
  B.Genarray.fill(empty,0);
  structuredClone(emptyData.buffer,{transfer:[emptyData.buffer]});
  reject('detached-empty-buffer',()=>B.Genarray.fill(empty,0));
  return {cases, count:cases.length, float16:B.float16!==undefined, shared_buffer:true, resizable_buffer:true};
};
