# FPowerKit 配电网运算组件
**本仓库已上线PyPI**，您可以通过`pip install fpowerkit`直接以Python包的形式安装使用本仓库的代码！

## 安装
不同的体验所需的安装命令有所不同：

|体验|安装命令|
|---|---|
|仅电网描述|`pip install fpowerkit`|
|导纳矩阵和牛顿法|`pip install fpowerkit[newton]`|
|OpenDSS求解|`pip install fpowerkit[dss]`|
|DistFlow模型|`pip install fpowerkit[distflow]`|
|完整版|`pip install fpowerkit[full]`|

二次开发请使用完整版体验。

## 简介
- FPowerKit是一个配电网求解组件，它包含电网的描述(含母线、发电机、线路、光伏、风机和储能等)和多种内置和外部求解方案：
    + (内置) 改进DistFlow配电网最优潮流 ([原理介绍](docs/principle.md))
    + (内置) Newton-Raphson潮流计算
    + (外接) OpenDSS配电网潮流计算
    + 最优潮流+潮流计算核验的混合方案
- 对于最优潮流模型，优化目标为“发电成本最小”。发电成本模型为二次函数$f(x)=ax^2+bx+c$或者一次函数$f(x)=bx+c$。
- 依赖于feasytools和numpy: `pip install feasytools numpy`
- 内含IEEE 33节点配电网和IEEE 69节点配电网，可通过以下方式快速创建：
```py
from fpowerkit import PDNCases
grid_obj33 = PDNCases.IEEE33()
grid_obj69 = PDNCases.IEEE69()
```

## 重要信息目录
+ [FPowerKit文件格式](docs/xml_file.md)
+ [在命令行中使用](docs/cmd.md)
+ [从代码创建和求解电网](docs/develop.md)

## 引用说明
这个项目是[V2Sim](https://gitee.com/fmy_xfk/v2sim)的附属项目。V2Sim的论文请见如下链接

- 正式版：https://ieeexplore.ieee.org/document/10970754

- 早期版本：https://arxiv.org/abs/2412.09808

如果你正在使用本项目中的**改进配电网DistFlow模型**，请引用[V2Sim正式版论文](https://ieeexplore.ieee.org/document/10970754)：

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

IEEE33和IEEE69节点的配网数据从公开渠道收集。除配网数据以外，本仓库代码均遵循LGPL3.0协议使用。
