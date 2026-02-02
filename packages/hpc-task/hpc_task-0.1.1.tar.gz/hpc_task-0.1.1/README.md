# HPC Task
 
Python package for easy HPC task management based on paramiko.

## Installation

pip install -U hpc_task

**Requirements**
* paramiko
* ase

## Usage

```
import ase
from hpc_task.hpc import HPCTask
from hpc_task.hpc_calculator.vasp import Vasp as hpc_Vasp  # 必须导入hpc_Vasp 而非原生的 ase 的 Vasp

target_host = {
    'hostname': "TARGET HOST IP",
    'port': 22, 
    'username': "YOUR_USERNAME",
    'password': "YOUR_PASSWD", 
}

workdir = 'test_vasp_calc'
hpc = HPCTask(workdir=workdir)
hpc.scriptdir = '/data/bin/remote.job'  # 提交作业的脚本
hpc.connect(target_host)
# 启动队列，得到 jobid
hpc.prerun()
jobid = hpc.jobid
hpc.close()  # 此时可以关闭 ssh 通道

# 在运行时候再重新构造和连接 hpc
hpc = HPCTask(jobid=jobid)  # workdir 会根据 jobid 提取得到
hpc.connect(target_host)

# 结构、计算参数设置
atoms = ase.Atoms('N2', positions=[(0., 0., 0.), (1.4, 0., 0.)],
                  cell=[10, 10, 10], pbc=True)
# calc 设置
calc = hpc_Vasp(  
            xc='pbe',
            command='mpirun -np 8 vasp544_std',  # 必须设置，或者提供了 ASE vasp 的相关设置
            hpctask=hpc,  # 这个非常关键，必须提供
            gamma=True,
            encut=400,
            lwave=False,
            lcharg=False,
            )
# 计算
atoms.calc = calc
e = atoms.get_potential_energy()
print(f"Energy of N2 is {e} eV.")
# finish job，结束节点任务
hpc.postrun()
# 关闭通道
hpc.close()
```

## TODO
