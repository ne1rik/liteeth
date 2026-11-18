from migen import *
from litex.gen.sim import run_simulation
from liteeth.frontend.etherbone import (
    LiteEthEtherboneWishboneMaster, LiteEthEtherboneWishboneSlave)

def set_opt(ep, name, val):
    if hasattr(ep, name):
        yield getattr(ep, name).eq(val)

def master_case(err, ack, cycles=60):
    dut = LiteEthEtherboneWishboneMaster(); tr=[]
    def gen():
        yield dut.sink.valid.eq(1); yield dut.sink.we.eq(0)
        yield dut.sink.last.eq(1);  yield dut.sink.count.eq(1)
        yield dut.sink.addr.eq(0x10); yield dut.sink.base_addr.eq(0)
        yield from set_opt(dut.sink,'byte_enable',0xf)
        yield from set_opt(dut.sink,'be',0xf)
        yield from set_opt(dut.sink,'last_be',0xf)
        yield dut.source.ready.eq(1)
        yield dut.bus.err.eq(err); yield dut.bus.ack.eq(ack)
        yield dut.bus.dat_r.eq(0xDEADBEEF)
        for _ in range(cycles):
            tr.append(((yield dut.bus.cyc),(yield dut.source.valid)))
            yield
    run_simulation(dut, gen()); return tr

def slave_case(resp, cycles=60):
    dut = LiteEthEtherboneWishboneSlave(); tr=[]
    def gen():
        yield dut.bus.cyc.eq(1); yield dut.bus.stb.eq(1); yield dut.bus.we.eq(0)
        yield dut.bus.adr.eq(0x10); yield dut.bus.sel.eq(0xf)
        yield dut.source.ready.eq(1); yield dut.sink.valid.eq(0)
        for i in range(cycles):
            if resp and i==10:
                yield dut.sink.valid.eq(1); yield dut.sink.we.eq(1)
                yield dut.sink.data.eq(0xCAFEBABE)
            tr.append((yield dut.bus.ack)); yield
    run_simulation(dut, gen()); return tr

m_err = master_case(1,0); m_ack = master_case(0,1)
s_lost= slave_case(False); s_ok = slave_case(True)
print("MASTER err: cyc-high=%d/60 src_valid=%d  => %s"%(sum(c for c,_ in m_err),sum(v for _,v in m_err),"DEADLOCK" if sum(v for _,v in m_err)==0 else "ok"))
print("MASTER ack: cyc-high=%d/60 src_valid=%d  => ok"%(sum(c for c,_ in m_ack),sum(v for _,v in m_ack)))
print("SLAVE lost: ack=%d => %s"%(sum(s_lost),"HANG" if sum(s_lost)==0 else "ok"))
print("SLAVE resp: ack=%d => ok"%sum(s_ok))
