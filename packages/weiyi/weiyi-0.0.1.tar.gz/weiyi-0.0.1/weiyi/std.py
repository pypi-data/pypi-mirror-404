#ISA

H = 1
P = 2
nop = lambda hp=0: (13+hp)<<20

#I(0~0xFF)/G(0x100~0x1FF)
ghi = lambda rd, imm: ((rd&0xFF)<<24)|(5<<18)|((imm>>20)&0xFFF)  #G
glo = lambda rd, imm: ((rd&0xFF)<<24)|(8<<18)|(imm&0xFFFFF)  #G
alu = lambda opc, rd, r0, r1: ((rd&0xFF)<<24)|(opc<<18)|(((r0>>8)&1)<<17)|(((r1>>8)&1)<<16)|((r0&0xFF)<<8)|(r1&0xFF)  #G,IG,IG
add = lambda rd, r0, r1: alu(12, rd, r0, r1)
sub = lambda rd, r0, r1: alu(13, rd, r0, r1)
bor = lambda rd, r0, r1: alu(2, rd, r0, r1)
and_ = lambda rd, r0, r1: alu(0, rd, r0, r1)
xor = lambda rd, r0, r1: alu(3, rd, r0, r1)
neq = lambda rd, r0, r1: alu(16, rd, r0, r1)
equ = lambda rd, r0, r1: alu(17, rd, r0, r1)
lst = lambda rd, r0, r1: alu(18, rd, r0, r1)
lse = lambda rd, r0, r1: alu(19, rd, r0, r1)
shl = lambda rd, r0, r1: alu(20, rd, r0, r1)
shr = lambda rd, r0, r1: alu(21, rd, r0, r1)
rol = lambda rd, r0, r1: alu(22, rd, r0, r1)
sar = lambda rd, r0, r1: alu(23, rd, r0, r1)
cad = lambda rd, r0, r1: alu(14, rd, r0, r1)
csb = lambda rd, r0, r1: alu(15, rd, r0, r1)
opl = lambda r0, r1: (7<<18)|(1<<17)|(((r1>>8)&1)<<16)|((r0&0xFF)<<8)|(r1&0xFF)  #G,IG
opr = lambda opc, rd: ((rd&0xFF)<<24)|(7<<18)|opc  #G
plo = lambda rd: opr(0)
phi = lambda rd: opr(1)
div = lambda rd: opr(2)
mod = lambda rd: opr(3)

#C(0x200~0x2FF)/N(0x300~0x3FF)
csr = lambda rd, r0: ((rd&0xFF)<<24)|(4<<18)|(r0&0xFF)  #G,C
chi = lambda rd, imm: ((rd&0xFF)<<24)|(8<<20)|((imm>>20)&0xFFF)  #C
clo = lambda rd, imm, hp=0: ((rd&0xFF)<<24)|((9+hp)<<20)|(imm&0xFFFFF)  #C
sfs = lambda rd, r0: ((rd&0xFF)<<24)|(8<<20)|((8+((r0>>8)&1))<<16)|(r0&0xFF)  #C,IG
amk = lambda rd, r0, r1, hp=0: ((rd&0xFF)<<24)|((13+hp)<<20)|((((r1>>8)&1)^(r1>>9))<<18)|(((r0>>9)^1)<<17)|(((r1>>9)^1)<<16)|((r0&0xFF)<<8)|(r1&0xFF)  #C,GN,IGCN

#CSR/SBF

#r00 = g20 = 0x120
#rdf = gff = 0x1FF
#n00 = 0x300
#nff = 0x3FF
ptr = 0x200
lnk = 0x201
rsm = 0x202
rsm_master = 0x310
rsm_monitor = 0x320
rsm_timer = 0x340
exc = 0x203
exc_halt = 0x310
exc_resume = 0x320
exc_tcs = 0x340
exc_byzero = 0x380
exc_ich = 0x312
exc_dch = 0x322
exc_unaligned = 0x342
exc_fifo = 0x382
ehn = 0x204
stk = 0x205
icf = 0x206
ica = 0x207
icd = 0x208
dcf = 0x209
dca = 0x20A
dcd = 0x20B
nex = 0x20C
nex_adr = 0x20
nex_bce = 0x21
nex_rta = 0x22
nex_rtd = 0x23
frm = 0x20D
frm_pl1 = 0
frm_pl0 = 1
frm_tag = 2
frm_dst = 3
scp = 0x20E
scp_mem = 0
scp_tgm = 1
scp_cdm = 2
scp_cod = 3
tim = 0x20F
wcl = 0x210
wcl_now = 0
wcl_bgn = 1
wcl_end = 2
wch = 0x211
wch_now = 0
wch_bgn = 1
wch_end = 2
led = 0x212
trm = 0x213

#BitField

lsb = lambda msk:(msk&-msk).bit_length()-1
def bfe(fld, val):
    msk = ((fld>>4)&0xF)<<((fld&0xF)<<1)
    sca = lsb(msk)
    return (val & (msk>>sca)) << sca
def bfd(fld, val):
    msk = ((fld>>4)&0xF)<<((fld&0xF)<<1)
    sca = lsb(msk)
    return (val>>sca) & (msk>>sca)
def abf(rd, fld, nib, hp=0):
    sca = lsb(((fld>>4)&0xF)<<((fld&0xF)<<1))    
    if sca & 1:
        sca -= 1
        nib <<= 1
    return amk(rd, fld, 0x300|((nib&0xF)<<4)|(sca>>1), hp)
to_signed = lambda rx, wid=32: -(rx & (1 << (wid - 1))) | (rx & ((1 << wid) - 1))
gli = lambda rd, imm: [glo(rd,imm)] if imm == to_signed(imm,20) else [glo(rd,imm),ghi(rd,imm)]
cli = lambda rd, imm, hp=0: [chi(rd,imm),clo(rd,imm,hp)]
        
#RTLink

rtlk_oper = lambda oper,narg=0: [*gli(0x1ff,0xFFFF),
    sfs(nex,nex_adr),
    nop(P),
    csr(0x1fe,nex),
    nop(),
    and_(0x1fe,0x1fe,0x1ff),
    *gli(0x1fd,narg<<16),
    nop(),
    add(0x1fe,0x1fe,0x1fd),
    sfs(frm,frm_dst),
    *cli(frm,1<<20),
    sfs(frm,frm_tag),
    amk(frm,0x101,0x1ff),
    sfs(frm,frm_pl0),
    amk(frm,0x101,0x1fe),
    sfs(frm,frm_pl1),
    amk(frm,0x101,oper)]

rtlk_info = lambda info,pld=0: [sfs(nex,nex_adr),
    nop(P),
    csr(0x1ff,nex),
    *gli(0x1fe,0xFFFF),
    nop(),
    and_(0x1ff,0x1ff,0x1fe),
    *gli(0x1fe,info<<20),
    nop(),
    add(0x1ff,0x1ff,0x1fe),
    *gli(0x1fe,4<<20),
    sfs(frm,frm_dst),
    *cli(frm,1<<20),
    sfs(frm,frm_tag),
    amk(frm,0x101,0x1fe),
    sfs(frm,frm_pl0),
    amk(frm,0x101,0x1ff),
    sfs(frm,frm_pl1),
    amk(frm,0x101,pld)]

rtlk_data = lambda pl0,pl1: [sfs(nex,nex_adr),
    nop(P),
    csr(0x1ff,nex),
    sfs(frm,frm_dst),
    *cli(frm,1<<20),
    sfs(frm,frm_tag),
    amk(frm,0x101,0x1ff),
    sfs(frm,frm_pl0),
    amk(frm,0x101,pl0),
    sfs(frm,frm_pl1),
    amk(frm,0x101,pl1)]

rtlk_exec = lambda code: [amk(exc,0x310,0x101,P)]+code+[amk(exc,0x310,0x100,P)]
    
def rtlk_dnld(code):
    code = code+rtlk_oper(0)+[nop(H),nop(H)]
    pos = len(code)
    code += rtlk_info(1,lnk)+rtlk_info(0,exc)+[nop(H),nop(H)]
    dnld = [clo(exc,1,P),
        chi(exc,0),
        chi(rsm,0),
        clo(rsm,1),
        glo(0x100,0),
        glo(0x101,-1),
        chi(ica,0)]
    for i in range(len(code)):
        dnld += [clo(ica,i),chi(icd,code[i]),clo(icd,code[i])]
    return dnld+[amk(exc,0x300,exc),
        amk(ptr,0x320,0,P),
        *cli(ehn,pos),
        amk(stk,0x320,0),
        amk(exc,0x310,0x300,P)]
        
W_CHN_ADR = 5
W_NOD_ADR = 16
W_TAG_LTN = 20
N_FRM_PLD = 2
W_FRM_PAD = 4
N_BYT = (3+W_CHN_ADR+W_NOD_ADR+W_TAG_LTN+N_FRM_PLD*32+W_FRM_PAD)//8

def pack_frame(flg, chn, adr, tag, pld, pad=0):
    nhdr = N_BYT - 4*N_FRM_PLD
    hdr = None
    if isinstance(tag, int):
        hdr = ((flg & ((1 << 3) - 1)) << (W_CHN_ADR + W_NOD_ADR + W_TAG_LTN)) | \
                    ((chn & ((1 << W_CHN_ADR) - 1)) << (W_NOD_ADR + W_TAG_LTN)) | \
                    ((adr & ((1 << W_NOD_ADR) - 1)) << W_TAG_LTN) | \
                    (tag & ((1 << W_TAG_LTN) - 1))
        hdr = hdr.to_bytes(nhdr,'big')
        tag = [tag] 
    lpd = len(pld)
    ltg = len(tag)
    if lpd % 2 == 1:
        pld += [0]
        lpd += 1
    dlt = lpd // 2 - ltg
    if dlt > 0:
        tag += [tag[-1]] * dlt
        ltg += dlt
    if hdr is None:
        hdr = [( ((flg & ((1 << 3) - 1)) << (W_CHN_ADR + W_NOD_ADR + W_TAG_LTN)) | \
                ((chn & ((1 << W_CHN_ADR) - 1)) << (W_NOD_ADR + W_TAG_LTN)) | \
                ((adr & ((1 << W_NOD_ADR) - 1)) << W_TAG_LTN) | \
                (i & ((1 << W_TAG_LTN) - 1)) ).to_bytes(nhdr,'big') for i in tag]
    pad = b"\x00" * pad
    buf = bytearray()
    for i in range(ltg):
        buf += pad + (hdr[i] if type(hdr) is list else hdr)
        buf += int(pld[2*i]).to_bytes(4,'big')
        buf += int(pld[2*i+1]).to_bytes(4,'big')
    return buf
    
def unpack_frame(frm):
    fhdr = int.from_bytes(frm[0:-(N_FRM_PLD*4)], "big")
    fpld = frm[-(N_FRM_PLD*4):]
    tag = fhdr & ((1<<W_TAG_LTN)-1)
    temp = fhdr >> W_TAG_LTN
    adr = temp & ((1<<W_NOD_ADR)-1)
    temp = temp >> W_NOD_ADR
    chn = temp & ((1<<W_CHN_ADR)-1)
    temp = temp >> W_CHN_ADR
    flg = temp & ((1<<3)-1)
    pld = [0] * N_FRM_PLD
    for i in range(N_FRM_PLD):
        pld[i] = int.from_bytes(fpld[i*4:i*4+4], "big")
    return flg, chn, adr, tag, pld

verbose = True
info = {}
data = {}
oper = {}

def proc_info(pld):
    inf = pld[0] & ((1<<12)-1)
    temp = pld[0] >> 12
    chn = temp & ((1<<4)-1)
    temp = temp >> 4
    adr = temp & ((1<<16)-1)
    buf = info.get((chn<<16)+adr,None)
    if buf is None:
        buf = {}
        info[adr] = buf
    buf[inf] = pld[1]
    if inf == 0:
        print(f"Node #{adr}.{chn}: Exception occurred with flag 0x{buf[0]:08X} at address {buf.get(1,0)}.")
    return chn,adr,inf==0

def proc_data(chn, adr, pld):
    adr += chn<<16
    buf = data.get(adr,None)
    if buf is None:
        data[adr] = pld
    else:
        buf += pld
    return False
    
def proc_oper(chn, pld):
    narg,adr = pld[0]>>16,pld[0]&0xffff
    buf = data.get((chn<<16)+adr,[])
    fin = False
    if pld[1] == 0:
        if narg == 0:
            if verbose:
                print(f"Node #{adr}.{chn}: Task complete.")
            fin = True
        elif narg == 1:
            if verbose:
                print(f"Node #{adr}.{chn}: Task running.")
    else:
        func = oper.get(pld[1],None)
        if callable(func):
            func(buf if narg == 0 else buf[-narg:],adr,chn)
            if narg > 0:
                data[(chn<<16)+adr] = buf[:-narg]
    return adr,fin
                
def monitor(nodes, tout, dev_rd):
    data.clear()
    mon = set(nodes)
    tot_cnt = 0
    while len(mon):
        frm = dev_rd()
        if frm is None or len(frm) < N_BYT:
            tot_cnt += 1
            if tot_cnt == tout:
                break
            else:
                continue
        flg,chn,adr,tag,pld = unpack_frame(frm)
        if flg == 4:
            chn,adr,fin = proc_info(pld)
        else:
            chn,adr = tag>>16,tag&0xffff
            if adr == 0xffff:
                adr,fin = proc_oper(chn,pld)
            else:
                fin = proc_data(chn,adr,pld)
        if fin:
            mon.remove(adr)
    return data
                            
if __name__ == '__main__':
    code = [
        add(0x120,0x100,0x121),
        clo(ptr, 4, P),
    ]
    print(code)
    print(pack_frame(4,0,0,0,code))