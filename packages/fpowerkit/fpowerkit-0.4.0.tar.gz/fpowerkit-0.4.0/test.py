import os
from dataclasses import dataclass
from typing import Dict, List, Optional, TextIO

@dataclass
class TimeSlice:
    obj: Optional[float]
    bus: Dict[str, List[float]]
    line: Dict[str, List[float]]
    gen: Dict[str, List[float]]
    pvwind: Dict[str, List[float]]
    ess: Dict[str, List[float]]

def read_module(f:TextIO):
    ln = f.readline().strip()
    if not ln:
        return "", {}
    op, cnt = ln.split()
    if op.upper() == "OBJ":
        return op, {"obj": [float(cnt)]}
    data = {}
    f.readline()  # header
    for i in range(int(cnt)):
        items = f.readline().strip().split()
        data[items[0]] = [float(x) for x in items[1:]]
    return op, data

def read_timeslice(f:TextIO) -> TimeSlice:
    obj = None
    bus_data = {}
    line_data = {}
    gen_data = {}
    pvwind_data = {}
    ess_data = {}

    while True:
        op, data = read_module(f)
        op = op.upper()
        if op == "OBJ":
            obj = data["obj"][0]
        elif op == "BUS":
            bus_data = data
        elif op == "LINE":
            line_data = data
        elif op == "GEN":
            gen_data = data
        elif op == "PVWIND":
            pvwind_data = data
        elif op == "ESS":
            ess_data = data
        else:
            break

    return TimeSlice(
        obj=obj,
        bus=bus_data,
        line=line_data,
        gen=gen_data,
        pvwind=pvwind_data,
        ess=ess_data
    )

def load_result(file_path: str):
    f = open(file_path)
    slices:List[TimeSlice] = []
    while True:
        ln = f.readline().strip()
        if not ln:
            break
        if ln.startswith("Time "):
            ts = read_timeslice(f)
            slices.append(ts)
    f.close()
    return slices

def __cmp(x1, x2):
    if x1 is None and x2 is None:
        return True
    if x1 is None or x2 is None:
        return False
    return abs(x1 - x2) < 1e-4

def compare(file1:str, file2:str):
    r1 = load_result(file1)
    r2 = load_result(file2)
    assert len(r1) == len(r2), "Number of time slices differ"
    for s1, s2 in zip(r1, r2):
        assert __cmp(s1.obj, s2.obj), "Objective values differ: {} vs {}".format(s1.obj, s2.obj)
        for mod in ['bus', 'line', 'gen', 'pvwind', 'ess']:
            d1 = getattr(s1, mod)
            d2 = getattr(s2, mod)
            assert d1.keys() == d2.keys(), f"{mod} IDs differ"
            for key in d1.keys():
                vals1 = d1[key]
                vals2 = d2[key]
                assert len(vals1) == len(vals2), f"Number of values for {mod} ID {key} differ"
                for v1, v2 in zip(vals1, vals2):
                    if abs(v1 - v2) > 1e-4:
                        print(f"Difference found in {mod} ID {key}: {v1} vs {v2}")
                        return 1
    return 0

def test_one(case_name:str, output_file:str, answer_file:str, extra_opts:str=""):
    print(f"Test {case_name}: {extra_opts}")
    os.system(f'python main.py -g cases/{case_name} -o test/{output_file} {extra_opts}')
    diffs = compare(f'test/{output_file}', answer_file)
    if diffs == 0:
        print(f"  Test passed for {output_file}")
    else:
        print(f"  Test failed for {output_file} with {diffs} diffs")

if __name__ == "__main__":
    print("Testing...")
    print("2islands DistFlow")
    os.system('python main.py -g cases/2islands.xml -o test/2islands_d.out -m DistFlow')

    test_one("33base.xml", "33base_df.out", 'test/33base_df.ans', "-m DistFlow")
    # test_one("33base.xml", "33base_ldf2.out", 'test/33base_ldf.ans', "-m LinDistFlow2")
    test_one("33base.xml", "33base_ldf.out", 'test/33base_ldf.ans', "-m LinDistFlow")
    test_one("33base.xml", "33base_nt.out", 'test/33base_nt.ans', "-m Newton")

    print("33mulg DistFlow")
    os.system('python main.py -g cases/33mulg.xml -o test/33mulg_d.out -m DistFlow -b 0 -e 86400 -s 3600')
    print("33pvwd DistFlow")
    os.system('python main.py -g cases/33pvwd.xml -o test/33pvwd_d.out -m DistFlow -b 0 -e 86400 -s 3600')
    print("33esss DistFlow")
    os.system('python main.py -g cases/33esss.xml -o test/33esss_d.out -m DistFlow -b 0 -e 86400 -s 3600')