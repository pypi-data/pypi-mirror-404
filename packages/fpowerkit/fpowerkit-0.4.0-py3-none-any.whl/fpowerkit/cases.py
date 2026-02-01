from typing import List, Tuple
from feasytools import SegFunc, ConstFunc
from .grid import GeneratorModel, Grid, Bus, Line

# IEEE33 kVA
_IEEE33_LOAD = [
    (1,0,0),
    (2,100.00,60.00),
    (3,90.00,40.00),
    (4,120.00,80.00),
    (5,60.00,30.00),
    (6,60.00,20.00),
    (7,200.00,100.00),
    (8,200.00,100.00),
    (9,60.00,20.00),
    (10,60.00,20.00),
    (11,45.00,30.00),
    (12,60.00,35.00),
    (13,60.00,35.00),
    (14,120.00,80.00),
    (15,60.00,10.00),
    (16,60.00,20.00),
    (17,60.00,20.00),
    (18,90.00,40.00),
    (19,90.00,40.00),
    (20,90.00,40.00),
    (21,90.00,40.00),
    (22,90.00,40.00),
    (23,90.00,50.00),
    (24,420.00,200.00),
    (25,420.00,200.00),
    (26,60.00,25.00),
    (27,60.00,25.00),
    (28,60.00,20.00),
    (29,120.00,70.00),
    (30,200.00,600.00),
    (31,150.00,70.00),
    (32,210.00,100.00),
    (33,60.00,40.00)
]

# IEEE69 kVA
_IEEE69_LOAD = [
    (1, 0, 0),
    (2, 0, 0),
    (3, 0, 0),
    (4, 0, 0),
    (5, 0, 0),
    (6, 2.6, 2.2),
    (7, 40.4, 30),
    (8, 75, 54),
    (9, 30, 22),
    (10, 28, 19),
    (11, 145, 104),
    (12, 145, 104),
    (13, 8, 5.5),
    (14, 8, 5.5),
    (15, 0, 0, 0),
    (16, 45.5, 30),
    (17, 60, 35),
    (18, 60, 35),
    (19, 0, 0, 0),
    (20, 1, 0.6),
    (21, 114, 81),
    (22, 5.5, 3.5),
    (23, 0, 0, 0),
    (24, 28, 20),
    (25, 0, 0, 0),
    (26, 14, 10),
    (27, 14, 10),
    (28, 26, 18.6),
    (29, 26, 18.6),
    (30, 0, 0, 0),
    (31, 0, 0, 0),
    (32, 0, 0, 0),
    (33, 14, 10),
    (34, 19.5, 14),
    (35, 6, 4),
    (36, 0, 0, 0),
    (37, 79, 56.4),
    (38, 384.7, 274.5),
    (39, 384.7, 274.5),
    (40, 40.5, 28.3),
    (41, 3.6, 3.7),
    (42, 4.35, 3.5),
    (43, 26.4, 19),
    (44, 24, 17.2),
    (45, 0, 0, 0),
    (46, 0, 0, 0),
    (47, 0, 0, 0),
    (48, 100, 72),
    (49, 0, 0, 0),
    (50, 1244, 888),
    (51, 32, 23),
    (52, 0, 0, 0),
    (53, 227, 162),
    (54, 59, 42),
    (55, 18, 13),
    (56, 18, 13),
    (57, 28, 20),
    (58, 28, 20),
    (59, 26, 18.55),
    (60, 26, 18.55),
    (61, 0, 0, 0),
    (62, 24, 17),
    (63, 24, 17),
    (64, 1.2, 1),
    (65, 0, 0, 0),
    (66, 6, 4.3),
    (67, 0, 0, 0),
    (68, 39.22, 26.3),
    (69, 39.22, 26.3),
]

_DEFAULT_LOAD_SCALE = [
    (0*3600, 0.7),
    (1*3600, 0.65),
    (2*3600, 0.625),
    (3*3600, 0.625),
    (4*3600, 0.625),
    (5*3600, 0.6),
    (6*3600, 0.725),
    (7*3600, 0.9),
    (8*3600, 1.15),
    (9*3600, 1.6),
    (10*3600, 2.025),
    (11*3600, 2.2),
    (12*3600, 2.25),
    (13*3600, 1.8),
    (14*3600, 1.0),
    (15*3600, 1.725),
    (16*3600, 1.975),
    (17*3600, 2.3),
    (18*3600, 2.425),
    (19*3600, 2.5),
    (20*3600, 1.95),
    (21*3600, 1.4),
    (22*3600, 1.0),
    (23*3600, 0.8),
]

_IEEE33_LINE = [
    (1,1,2,0.0922,0.047),
    (2,2,3,0.493,0.2511),
    (3,3,4,0.366,0.1864),
    (4,4,5,0.3811,0.1941),
    (5,5,6,0.819,0.707),
    (6,6,7,0.1872,0.6188),
    (7,7,8,0.7114,0.2351),
    (8,8,9,1.03,0.74),
    (9,9,10,1.044,0.74),
    (10,10,11,0.1966,0.065),
    (11,11,12,0.3744,0.1238),
    (12,12,13,1.468,1.155),
    (13,13,14,0.5416,0.7129),
    (14,14,15,0.591,0.526),
    (15,15,16,0.7463,0.545),
    (16,16,17,1.289,1.721),
    (17,17,18,0.732,0.574),
    (18,2,19,0.164,0.1565),
    (19,19,20,1.5042,1.3554),
    (20,20,21,0.4095,0.4784),
    (21,21,22,0.7089,0.9373),
    (22,3,23,0.4512,0.3083),
    (23,23,24,0.898,0.7091),
    (24,24,25,0.896,0.7011),
    (25,6,26,0.203,0.1034),
    (26,26,27,0.2842,0.1447),
    (27,27,28,1.059,0.9337),
    (28,28,29,0.8042,0.7006),
    (29,29,30,0.5075,0.2585),
    (30,30,31,0.9744,0.963),
    (31,31,32,0.3105,0.3619),
    (32,32,33,0.341,0.5302),
]

_IEEE69_LINE = [
    (1, 1, 2, 0.0005, 0.0012),
    (2, 2, 3, 0.0005, 0.0012),
    (3, 3, 4, 0.0015, 0.0036),
    (4, 4, 5, 0.0251, 0.0294),
    (5, 5, 6, 0.366, 0.1864),
    (6, 6, 7, 0.3811, 0.1941),
    (7, 7, 8, 0.0922, 0.047),
    (8, 8, 9, 0.0493, 0.0251),
    (9, 9, 10, 0.819, 0.2707),
    (10, 10, 11, 0.1872, 0.0619),
    (11, 11, 12, 0.7114, 0.2351),
    (12, 12, 13, 1.03, 0.34),
    (13, 13, 14, 1.044, 0.345),
    (14, 14, 15, 1.058, 0.3496),
    (15, 15, 16, 0.1966, 0.065),
    (16, 16, 17, 0.3744, 0.1238),
    (17, 17, 18, 0.0047, 0.0016),
    (18, 18, 19, 0.3267, 0.1083),
    (19, 19, 20, 0.2106, 0.0696),
    (20, 20, 21, 0.3416, 0.1129),
    (21, 21, 22, 0.014, 0.0046),
    (22, 22, 23, 0.1591, 0.0526),
    (23, 23, 24, 0.3463, 0.1145),
    (24, 24, 25, 0.7488, 0.2475),
    (25, 25, 26, 0.3089, 0.1021),
    (26, 26, 27, 0.1732, 0.0572),
    (27, 3, 28, 0.0044, 0.0108),
    (28, 28, 29, 0.064, 0.1565),
    (29, 29, 30, 0.3978, 0.1315),
    (30, 30, 31, 0.0702, 0.0232),
    (31, 31, 32, 0.351, 0.116),
    (32, 32, 33, 0.839, 0.2816),
    (33, 33, 34, 1.708, 0.5646),
    (34, 34, 35, 1.474, 0.4873),
    (35, 4, 36, 0.0034, 0.0084),
    (36, 36, 37, 0.0851, 0.2083),
    (37, 37, 38, 0.2898, 0.7091),
    (38, 38, 39, 0.0822, 0.2011),
    (39, 8, 40, 0.0928, 0.0473),
    (40, 40, 41, 0.3319, 0.1114),
    (41, 9, 42, 0.174, 0.0886),
    (42, 42, 43, 0.203, 0.1034),
    (43, 43, 44, 0.2842, 0.1447),
    (44, 44, 45, 0.2813, 0.1433),
    (45, 45, 46, 1.59, 0.5337),
    (46, 46, 47, 0.7837, 0.263),
    (47, 47, 48, 0.3042, 0.1006),
    (48, 48, 49, 0.3861, 0.1172),
    (49, 49, 50, 0.5075, 0.2585),
    (50, 50, 51, 0.0974, 0.0496),
    (51, 51, 52, 0.145, 0.0738),
    (52, 52, 53, 0.7105, 0.3619),
    (53, 53, 54, 1.041, 0.5302),
    (54, 11, 55, 0.2012, 0.0611),
    (55, 55, 56, 0.0047, 0.0014),
    (56, 12, 57, 0.7394, 0.2444),
    (57, 57, 58, 0.0047, 0.0016),
    (58, 3, 59, 0.0044, 0.0108),
    (59, 59, 60, 0.064, 0.1565),
    (60, 60, 61, 0.1053, 0.123),
    (61, 61, 62, 0.0304, 0.0355),
    (62, 62, 63, 0.0018, 0.0021),
    (63, 63, 64, 0.7283, 0.8509),
    (64, 64, 65, 0.31, 0.3623),
    (65, 65, 66, 0.041, 0.0478),
    (66, 66, 67, 0.0092, 0.0116),
    (67, 67, 68, 0.1089, 0.1373),
    (68, 68, 69, 0.0009, 0.0012),
    (69, 11, 66, 0.5, 0.5),
    (70, 13, 21, 0.5, 0.5),
    (71, 15, 69, 1, 0.5),
    (72, 39, 48, 2, 1),
    (73, 27, 54, 1, 0.5),
]

_DEFAULT_GEN_POS = [1,2,3,6,8]

_DEFAULT_GENERATOR = GeneratorModel(0, 30, -30, 30, 0.0001, 0.3, 10)

def _create_load(s:float, scales:'list[tuple[int, float]]'):
    return SegFunc([(p[0],p[1]*s) for p in scales])

def _get_buses(
        Sb_KVA:float, grid_repeat:int, 
        LOAD:'list[tuple[int,float,float]]', 
        changeable_load:bool, 
        load_fluc:'list[tuple[int,float]]', 
        load_repeat:int,
        load_period:int,
    ):
    if changeable_load:
        if len(load_fluc) == 0:
            for j in range(24):
                load_fluc.append((_DEFAULT_LOAD_SCALE[j][0], _DEFAULT_LOAD_SCALE[j][1]))
        else:
            ls = load_fluc
            load_fluc = []
            for j in range(24):
                load_fluc.append((ls[j][0], ls[j][1]))
        if grid_repeat == 1:
            B = [Bus(
                "b" + str(p[0]), 
                _create_load(p[1] / Sb_KVA, load_fluc).repeat(load_repeat, load_period),
                _create_load(p[2] / Sb_KVA, load_fluc).repeat(load_repeat, load_period),
                (i % 10) * 50, (i // 10) * 50,
                min_v_pu=0.9, max_v_pu=1.1
            ) for i, p in enumerate(LOAD)]
        else:
            B = []
            for i in range(grid_repeat):
                pre = len(LOAD) * i
                B.extend([Bus(
                    f"b{i}_{p[0]}", 
                    _create_load(p[1] / Sb_KVA, load_fluc).repeat(load_repeat, load_period),
                    _create_load(p[2] / Sb_KVA, load_fluc).repeat(load_repeat, load_period),
                    ((pre + j) % 10) * 50, ((pre + j) // 10) * 50,
                    min_v_pu=0.9, max_v_pu=1.1
                ) for j, p in enumerate(LOAD)])
    else:
        if grid_repeat == 1:
            B = [Bus(
                f"b{p[0]}", 
                p[1] / Sb_KVA,
                p[2] / Sb_KVA,
                (i % 10) * 50, (i // 10) * 50,
                min_v_pu=0.9, max_v_pu=1.1
            ) for i, p in enumerate(LOAD)]
        else:
            B = []
            for i in range(grid_repeat):
                pre = len(LOAD) * i
                B.extend([Bus(
                    f"b{i}_{p[0]}", 
                    p[1] / Sb_KVA, 
                    p[2] / Sb_KVA, 
                    ((pre + j) % 10) * 50, ((pre + j) // 10) * 50,
                    min_v_pu=0.9, max_v_pu=1.1
                ) for j, p in enumerate(LOAD)])
    B[0].fixV(1.0)
    B[0].Pd = ConstFunc(0)
    B[0].Qd = ConstFunc(0)
    B[0].MaxV = float('inf')
    B[0].MinV = 0
    return B

def _get_lines(Zb:float, LINE:List[Tuple[int, int, int, float, float]], grid_repeat:int):
    if grid_repeat == 1:
        L = [Line("l"+str(p[0]), "b"+str(p[1]), "b"+str(p[2]), p[3]/Zb, p[4]/Zb) for p in LINE]
    else:
        L = []
        for i in range(grid_repeat):
            L.extend([Line(f"l{i}_{p[0]}", f"b{i}_{p[1]}", f"b{i}_{p[2]}", p[3]/Zb, p[4]/Zb) for p in LINE])
    return L

def _get_gens(default_gen:GeneratorModel, gen_pos:'list[int]', grid_repeat:int):
    if grid_repeat == 1:
        G = [default_gen.toGenerator(
            "g" + p, "b" + p, (i % 10) * 50, (i // 10) * 50
        ) for i, p in enumerate(map(str, gen_pos))]
    else:
        G = []
        for i in range(grid_repeat):
            pre = len(gen_pos) * i
            G.extend([
                default_gen.toGenerator(
                    f"g{i}_{p}", f"b{i}_{p}", ((pre + j) % 10) * 50, ((pre + j) // 10) * 50
                ) for j, p in enumerate(gen_pos)
            ])
    return G

class PDNCases:
    @staticmethod
    def IEEE33(
        Ub_kV:float=12.66,
        Sb_MVA:float=1,
        gen_pos:'list[int]'=_DEFAULT_GEN_POS,
        default_gen:GeneratorModel=_DEFAULT_GENERATOR,
        grid_repeat:int = 1,
        changeable_load:bool = False,
        load_fluc:'list[tuple[int, float]]' = [],
        load_repeat:int = 8,
        load_period:int = 86400
    ):
        '''IEEE 33-bus distribution network'''
        return Grid(Sb_MVA, Ub_kV, 
            _get_buses(Sb_MVA*1000, grid_repeat, _IEEE33_LOAD, changeable_load, load_fluc, load_repeat, load_period),
            _get_lines(Ub_kV**2/Sb_MVA, _IEEE33_LINE, grid_repeat),
            _get_gens(default_gen, gen_pos, grid_repeat),
            [],[]
        )
    
    @staticmethod
    def IEEE69(
        Ub_kV:float=10.0,
        Sb_MVA:float=1,
        gen_pos:'list[int]'=_DEFAULT_GEN_POS,
        default_gen:GeneratorModel=_DEFAULT_GENERATOR,
        grid_repeat:int = 1,
        changeable_load:bool = False,
        load_fluc:'list[tuple[int, float]]' = [],
        load_repeat:int = 8,
        load_period:int = 86400
    ):
        '''IEEE 69-bus distribution network'''
        return Grid(Sb_MVA, Ub_kV, 
            _get_buses(Sb_MVA*1000, grid_repeat, _IEEE69_LOAD, changeable_load, load_fluc, load_repeat, load_period),
            _get_lines(Ub_kV**2/Sb_MVA, _IEEE69_LINE, grid_repeat),
            _get_gens(default_gen, gen_pos, grid_repeat),
            [], []
        )

__all__ = ["PDNCases"]