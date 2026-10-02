const n=65536, a=Float64Array.from({length:n},(_,i)=>i),b=new Float64Array(n);
let sink=0;
function measure(name,bytes,f) {
  f();const times=[];
  for(let i=0;i<7;i++){const t=process.cpuUsage();f();const dt=process.cpuUsage(t);times.push((dt.user+dt.system)/1e6);}
  times.sort((a,b)=>a-b);console.log([name,times[3],bytes].join('\t'));
}
measure('scalar',1e6*8,()=>{let s=0;for(let i=0;i<1e6;i++)s+=a[i&65535];sink=s;});
measure('fill',1000*n*8,()=>{for(let i=0;i<1000;i++)b.fill(17);});
measure('blit',1000*n*8,()=>{for(let i=0;i<1000;i++)b.set(a);});
measure('views',0,()=>{for(let i=0;i<1e5;i++)sink=a.subarray(i&32767,(i&32767)+16)[0];});
measure('numeric',1e6*24,()=>{for(let i=0;i<1e6;i++){const j=i&65535;b[j]=.5*a[j]+b[j];}});
const ints=new Int32Array(n*2);for(let i=0;i<n;i++)ints[2*i]=i;
measure('int64',1e6*8,()=>{let lo=0,hi=0;for(let i=0;i<1e6;i++){const j=(i&65535)*2;const v=lo+(ints[j]>>>0);lo=v>>>0;hi=(hi+ints[j+1]+(v>0xffffffff?1:0))|0;}sink=hi*4294967296+lo;});
const z=new Float64Array(n*2);for(let i=0;i<n;i++){z[2*i]=i;z[2*i+1]=1;}
measure('complex',1e6*16,()=>{let s=0;for(let i=0;i<1e6;i++){const j=(i&65535)*2;s+=z[j]+z[j+1];}sink=s;});
if(!sink) throw Error('benchmark optimized away');
