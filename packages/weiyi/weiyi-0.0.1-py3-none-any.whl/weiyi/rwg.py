from .std import *

rsm_uart = 0x380
rsm_debug = 0x312
rsm_coproc = 0x322
rsm_spi = 0x342
rsm_gpio = 0x382
exc_pll = 0x314
fai = 0x213
fai_fgl = 0
fai_fgh = 1
fai_dnl = 2
fai_dnh = 3
fai_idl = 4
fai_idh = 5
fai_aux = 6
mac = 0x214
mac_mdi = 0
mac_dly = 1
mac_cfg = 2
mac_srl = 3
mac_srh = 4
mac_dsl = 5
mac_dsh = 6
cpr = 0x215
spi = 0x216
spi_slv = 4
spi_ctl = 5
rnd = 0x217
ttl = 0x218
dio = 0x219
dio_dir = 0
dio_inv = 1
dio_pos = 2
dio_neg = 3
ctr = 0x21A
csm = 0x21B
tts = 0x21C
tev = 0x21D
ubr = 0x21E
uda = 0x21F
dds = 0x220
dds_pfl0 = 0x370
dds_iou0 = 0x380
dds_pfl1 = 0x372
dds_iou1 = 0x382
dds_pfl2 = 0x374
dds_iou2 = 0x384
dds_pfl3 = 0x376
dds_iou3 = 0x386
dds_txe = 0x3F8
dds_ior = 0x3FA
dds_rst = 0x3FC
dds_synrst = 0x3FE
sbg = 0x221
sbg_pud0 = 0x310
sbg_iou0 = 0x320
sbg_pud1 = 0x312
sbg_iou1 = 0x322
sbg_pud2 = 0x314
sbg_iou2 = 0x324
sbg_pud3 = 0x316
sbg_iou3 = 0x326
sbg_mrk = 0x3F8
pdm = 0x222
pdm_rf0 = 0x3F0
pdm_rf1 = 0x3F2
pdm_rf2 = 0x3F4
pdm_rf3 = 0x3F6
cds = 0x223
cds_dly = 16
cds_sca = 17
cds_sca_sca0 = 0x3F0
cds_sca_sca1 = 0x3F2
cds_sca_sca2 = 0x3F4
cds_sca_sca3 = 0x3F6 
pof = 0x224
fte = 0x225
fte_dth = 0x3F0
fte_pha = 0x312
fte_ena = 0x322
fte_sel = 0x3FA
fte_hnz = 0x3FC
fte_rld = 0x3FE
ft0 = 0x226
ft1 = 0x227
ft2 = 0x228
ft3 = 0x229
ape = 0x22A
ap0 = 0x22B
ap1 = 0x22C
ap2 = 0x22D
ap3 = 0x22E
cmk = 0x22F
cfq = 0x230
cam = 0x231
    
def rwg_spi(chn, data=[0,0,0,0], size=1):
    return [sfs(spi,spi_slv),
    *cli(spi,chn<<1),
    sfs(spi,3),
    *cli(spi,data[3]),
    sfs(spi,2),
    *cli(spi,data[2]),
    sfs(spi,1),
    *cli(spi,data[1]),
    sfs(spi,0),
    *cli(spi,data[0]),
    sfs(spi,spi_ctl),
    *cli(spi,(3<<30)|(1<<20)|(0xFF<<8)|(size<<3)),
    *[nop(P) for i in range(21)],
    clo(dds,bfe(dds_iou0,chn)|bfe(dds_iou1,chn>>1)|
        bfe(dds_iou2,chn>>2)|bfe(dds_iou3,chn>>3))]
    
def rwg_carrier(chn, frq, amp=1, pha=0):
    ftw = round((frq/1000)*(1<<32))
    asf = round(amp*0xFF)
    phw = round(pha*0x10000)
    return rwg_spi(chn,[0,(ftw&0xFF)<<24,((phw&0xFF)<<24)|(ftw>>8),(14<<24)|(2<<18)|(asf<<8)|(phw>>8)],9)

def rwg_init(carriers, sca=(0,0,0,0)):
    return [clo(pdm,
        bfe(pdm_rf0,0)|bfe(pdm_rf1,0)|
        bfe(pdm_rf2,0)|bfe(pdm_rf3,0)),
    sfs(cds,cds_sca),
    clo(cds,bfe(cds_sca_sca0,sca[0])|bfe(cds_sca_sca1,sca[1])|
        bfe(cds_sca_sca2,sca[2])|bfe(cds_sca_sca3,sca[3])),
    *rwg_spi(0xF,[0,0,0x02<<24,0x00006020],5),
    *rwg_carrier(1,carriers[0]),
    *rwg_carrier(1<<1,carriers[1]),
    *rwg_carrier(1<<2,carriers[2]),
    *rwg_carrier(1<<3,carriers[3]),
    sfs(dio,dio_dir),
    amk(dio,0x101,0)]

def sbg_frq(sbn, frq, pha=0):
    return [sfs(fte,sbn),
    chi(fte,bfe(fte_rld,1)|bfe(fte_hnz,1<<1)),
    *cli(ft0,round(frq*0x100000000/250)),
    clo(pof,round(pha*0x1_00000)&0xFFFFF)]

def sbg_amp(sbn, amp):
    return [sfs(fte,sbn),
    chi(ape,bfe(fte_rld,1)|bfe(fte_hnz,1<<1)),
    clo(ap0,round(amp*0x7FFFFFFF)>>12)]

def sbg_ctrl(iou=0xF, pud=0xF, mrk=0):
    return [clo(sbg,
        bfe(sbg_iou0,iou)|bfe(sbg_iou1,iou>>1)|
        bfe(sbg_iou2,iou>>2)|bfe(sbg_iou3,iou>>3)|
        bfe(sbg_pud0,pud)|bfe(sbg_pud1,pud>>1)|
        bfe(sbg_pud2,pud>>2)|bfe(sbg_pud3,pud>>3)|
        bfe(sbg_mrk,mrk),P),
    nop(P)]