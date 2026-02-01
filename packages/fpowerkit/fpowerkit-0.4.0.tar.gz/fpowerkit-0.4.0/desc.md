# FPowerKit - A power distribution network calculation component

This is a package designed for power distribution network description and solving.

This package is affiliated to V2Sim, an open-aource microscopic V2G simulation platform in urban power and transportation network. If you are using the modified DistFlow model in this package, please cite the [paper](https://ieeexplore.ieee.org/document/10970754)：

```
@ARTICLE{10970754,
  author={Qian, Tao and Fang, Mingyu and Hu, Qinran and Shao, Chengcheng and Zheng, Junyi},
  journal={IEEE Transactions on Smart Grid}, 
  title={V2Sim: An Open-Source Microscopic V2G Simulation Platform in Urban Power and Transportation Network}, 
  year={2025},
  volume={16},
  number={4},
  pages={3167-3178},
  keywords={Vehicle-to-grid;Partial discharges;Microscopy;Batteries;Planning;Discharges (electric);Optimization;Vehicle dynamics;Transportation;Roads;EV charging load simulation;microscopic EV behavior;vehicle-to-grid;charging station fault sensing},
  doi={10.1109/TSG.2025.3560976}}
```

### Solvers available
There are multiple solvers can be used in FPowerKit.
- **Power flow calculation**
  - **Newton-Raphson**: Classical method for power flow calculation. **(GIL-free Compatible)**
  - **OpenDSS**: Call external OpenDSS for distribution network solving.
- **Optimal power flow (OPF)**
  - **DistFlow**: A classical OPF model for radial distribution network, with both quadratic and linear objective of minimal active generation cost.
  - **LinDistFlow**: A typical simplification of DistFlow.
  - **LinDistFlow2**: A **GIL-free compatible** version of LinDistFlow, only supporting linear objective.


There are also some abstract solvers for users to customize:
- **Combined Solver**: Combine two solvers to accomplish both OPF and accuracte power flow calculation. For example, use LinDistFlow + OpenDSS to get the optimal generation and the accurate power flow. The only GIL-free compatible combination is LinDistFlow2 + Newton.
- **Manual Solver**: Allow user to customize constraints

### Installation options
If you want to use different features, install with different command:

|Feature|Command|
|---|---|
|Only grid description|`pip install fpowerkit`|
|Y matrix & Newton|`pip install fpowerkit[newton]`|
|OpenDSS|`pip install fpowerkit[dss]`|
|DistFlow|`pip install fpowerkit[distflow]`|
|LinDistFlow|`pip install fpowerkit[ldf]`|
|All|`pip install fpowerkit[full]`|

Secondary development on this package requires all features.

### Introduction
There are 3 modes for this package to work:

- Optimal power flow (OPF): Use cvxpy to solve the optimal power flow and determine the output of the generators.

- Power flow calculation: Use OpenDSS/Newton-Raphson method to solve the power flow.

- Hybrid: Use OPF to determine the initial value, and then use OpenDSS/Newton-Raphson to perform accurate calculation.

Please visit https://gitee.com/fmy_xfk/fpowerkit to read the detailed introduction and the usage.