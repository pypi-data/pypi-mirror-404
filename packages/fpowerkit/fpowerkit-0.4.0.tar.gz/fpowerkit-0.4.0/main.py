import sys
import argparse
from feasytools import TimeFunc
from fpowerkit import *

OPF_MODEL = ['DistFlow','LinDistFlow','LinDistFlow2']
PF_MODEL = ['Newton','OpenDSS']
ALL_MODEL = OPF_MODEL + PF_MODEL

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Gurobi DistFlow Model Solver')
    parser.add_argument('-g',type=str,required=True,metavar="grid",help="path to a grid case zipfile")
    parser.add_argument('-o',type=str,required=False,metavar="output",help="Output file for the result", default="")
    parser.add_argument('-m',type=str,required=False,metavar='method',help="Newton, DistFlow, GridCal, or Combined", default="Combined")
    parser.add_argument('-b',type=int,required=False,metavar='begin',help="Solver begin time", default=0)
    parser.add_argument('-e',type=int,required=False,metavar='end',help="Solver end time", default=0)
    parser.add_argument('-s',type=int,required=False,metavar='step',help="Solver time step", default=300)
    parser.add_argument('-l',type=str,required=False,metavar='log',help="Items to be written in the log file", default="bus, gen, line, pvwind, ess")
    parser.add_argument('-sb',type=str,metavar='source_bus',help="Source bus/Slack bus ID for OpenDSS/GridCal solver", default="")
    opt = parser.parse_args()
    gr = Grid.fromFile(opt.g)

    if opt.o == "": 
        output = sys.stdout
        req_close = False
        print("Grid structure:")
        print(gr)
    else:
        output = open(opt.o,"w")
        req_close = True
    
    # Create Solver
    model = opt.m
    assert model in ALL_MODEL, f"Invalid solver method: {model}"
    if model == "DistFlow":
        svr = DistFlowSolver(gr)
    elif model == "Newton":
        svr = NewtonSolver(gr)
    elif model == "OpenDSS":
        svr = OpenDSSSolver(gr, source_bus=opt.sb.split(','))
    elif model == "Combined":
        svr = CombinedSolver(gr, source_bus=opt.sb)
    elif model == "LinDistFlow":
        svr = LinDistFlowSolver(gr)
    elif model == "LinDistFlow2":
        svr = LinDistFlow2Solver(gr)
    else:
        raise ValueError(f"Invalid solver: {model}")

    def _chk(x):
        if x is None: return "None"
        else: return f"{x:.4f}"
        
    logs = [x.strip().lower() for x in opt.l.split(',')]

    for t in range(opt.b,opt.e+1,opt.s):
        print(f"Time {t}:", file=output)
        ret, val = svr.solve(t)
        if ret:
            if model in OPF_MODEL:
                print(f"OBJ {val:.6f}", file=output)

            if "bus" in logs and len(gr.Buses)>0:
                print(f"BUS {len(gr.Buses)}", file=output)
                if model in OPF_MODEL:
                    print("BusID\tV/pu", file=output)
                    for bus in gr.Buses:
                        print(f"{bus.ID:5}\t{_chk(bus.V)}", file=output)
                else:
                    print("BusID\tV/pu\ttheta/rad", file=output)
                    for bus in gr.Buses:
                        print(f"{bus.ID:5}\t{_chk(bus.V)}\t{_chk(bus.theta)}", file=output)
            
            if "line" in logs and len(gr.Lines)>0:
                print(f"LINE {len(gr.Lines)}", file=output)
                print("LineID\tI/kA \tP/pu \tQ/pu ", file=output)
                for line in gr.Lines:
                    i = _chk(line.I*gr.Ib) if line.I is not None else "None"
                    print(f"{line.ID:6}\t{i}\t{_chk(line.P)}\t{_chk(line.Q)}", file=output)
            
            if isinstance(svr,DistFlowSolver) and len(svr.OverflowLines)>0:
                ofl = ','.join(map(str,svr.OverflowLines))
                print(f"Overflow lines: {ofl}", file=output)
            
            if model in OPF_MODEL:
                if "gen" in logs and len(gr.Gens)>0:
                    print(f"GEN {len(gr.Gens)}", file=output)
                    print(f"GenID\tP/pu \tQ/pu ", file=output)
                    for gen in gr.Gens:
                        p = gen.P(t) if isinstance(gen.P, TimeFunc) else gen.P
                        q = gen.Q(t) if isinstance(gen.Q, TimeFunc) else gen.Q
                        print(f"{gen.ID:5}\t{_chk(p)}\t{_chk(q)}", file=output)
                
                if "pvwind" in logs and len(gr.PVWinds)>0:
                    print(f"PVWIND {len(gr.PVWinds)}", file=output)
                    print("PVWID\tP/pu \tQ/pu \tCR/%  ", file=output)
                    for pvw in gr.PVWinds:
                        p = pvw.Pr
                        q = pvw.Qr
                        cr = pvw.CR
                        cr_str = f"{cr*100:.2f}%" if cr is not None else "None"
                        print(f"{pvw.ID:5}\t{_chk(p)}\t{_chk(q)}\t{cr_str}", file=output)
                
                if "ess" in logs and len(gr.ESSs)>0:
                    print(f"ESS {len(gr.ESSs)}", file=output)
                    print("ESSID\tP/pu \tQ/pu \tSOC/%  \tElec/puh", file=output)
                    for ess in gr.ESSs:
                        p = ess.P
                        q = ess.Q
                        soc = ess.SOC
                        elec = ess._elec
                        print(f"{ess.ID:5}\t{p:.4f}\t{q:.4f}\t{soc*100:.2f}%\t{elec:.4f}", file=output)
            gr.ApplyAllESS(opt.s)
        else:
            print("Fail", file=output)
    if req_close:
        output.close()