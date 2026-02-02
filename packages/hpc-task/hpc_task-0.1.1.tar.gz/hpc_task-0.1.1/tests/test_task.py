import os
import shutil
from pathlib import Path

import pytest
import ase
from hpc_task.hpc_calculator.vasp import Vasp as hpc_Vasp
from hpc_task.hpc_calculator.lasp import Lasp as hpc_Lasp
from hpc_task.hpc import HPCTask

if os.getenv("JUMP_HOST_IP"):
    jump_host = {
        'hostname': os.getenv("JUMP_HOST_IP"),
        'port': int(os.getenv("JUMP_HOST_PORT")),
        'username': os.getenv("JUMP_HOST_USER"),
        'password': os.getenv("JUMP_HOST_PASS"),  # 建议使用密钥认证而非密码
    }
else:
    jump_host = None

target_host = {
    'hostname': os.getenv("TARGET_HOST_IP"),
    'port': int(os.getenv("TARGET_HOST_PORT")),
    'username': os.getenv("TARGET_HOST_USER"),
    'password': os.getenv("TARGET_HOST_PASS"),  # 建议使用密钥认证而非密码
}

class TestHPCTask:
    def setup_method(self):
        pass

    def teardown_method(self):
        pass


    def test_connect(self):
        hpc = HPCTask()
        hpc.connect(target_host, jump_host)
        stdin, stdout, stderr = hpc.ssh_client.exec_command('hostname')
        print(hpc._remote_parent_workdir)
        print(stdout.read().decode().strip())
        hpc.close()

    def test_pre_post_run(self):
        workdir = 'test_hpc_run'
        hpc = HPCTask(workdir=workdir)
        hpc.scriptdir = '/data/bin/remote.job'
        hpc.connect(target_host, jump_host)
        stdin, stdout, stderr = hpc.prerun()
        jobid = hpc.jobid
        hpc.close()
        hpc = HPCTask(jobid=jobid)
        hpc.connect(target_host, jump_host)
        print(hpc.workdir)
        hpc.get_workdir()
        print(hpc.workdir)
        print(f"Job {hpc.jobid} status: {hpc.status}")
        stdin, stdout, stderr = hpc.postrun()
        print(stdout.read().decode().strip())

    def test_upload(self):
        workdir = 'test_hpc_run'
        hpc = HPCTask(workdir=workdir)
        hpc.connect(target_host, jump_host)
        # 在本地创建 workdir
        Path(workdir).mkdir(exist_ok=True)
        Path('test_hpc_run/sub-1').mkdir(exist_ok=True)
        Path('test_hpc_run/sub-2').mkdir(exist_ok=True)
        # 新建一个空文件
        with open('test_hpc_run/sub-1/test.xyz', 'w') as f:
            f.write('test')
        hpc.upload()

    def test_download(self):
        workdir = 'test_hpc_run'
        hpc = HPCTask(workdir=workdir)
        hpc.connect(target_host, jump_host)
        Path(workdir).mkdir(exist_ok=True)
        hpc.download()

    def test_hpc_vasp_calc(self):
        workdir = 'test_vasp_calc'
        # 队列占据
        hpc = HPCTask(workdir=workdir)
        #hpc.scriptdir = '$HOME/bin/hpc_job.chess'
        hpc.scriptdir = '/data/bin/remote.job'
        hpc.connect(target_host, jump_host)
        stdin, stdout, stderr = hpc.ssh_client.exec_command('hostname')
        hostname = stdout.read().decode().strip()
        print(hostname)
        stdin, stdout, stderr = hpc.prerun()
        print(stdout.read().decode().strip())
        print(f"Job {hpc.jobid} status: {hpc.status}")
        jobid = hpc.jobid
        hpc.close()
        # 结构、计算参数设置
        atoms = ase.Atoms('N2', positions=[(0., 0., 0.), (1.4, 0., 0.)], cell=[10, 10, 10], pbc=True)

        # calc 设置
        hpc = HPCTask(workdir=workdir, jobid=jobid)  # reconnect
        hpc.connect(target_host, jump_host)
        calc = hpc_Vasp(
                    directory=workdir,
                    xc='pbe',
                    #command='mpirun -np 8 -host $hostname vasp544_std',
                    command='mpirun -np 2 vasp_gam',
                    gamma=True,
                    encut=400,
                    lwave=False,
                    lcharg=False,
                    hpctask=hpc,  # 这个非常关键
                    )
        # 计算
        atoms.calc = calc
        e = atoms.get_potential_energy()
        print(f"Energy of N2 is {e} eV.")
        # finish job
        hpc.postrun()
        hpc.close()

    def test_hpc_lasp_calc(self):
        workdir = 'test_lasp_calc'
        Path(workdir).mkdir(parents=True, exist_ok=True)
        shutil.copyfile('CuCHO_lasp.in', Path(workdir)/'lasp.in')
        shutil.copyfile('CuCHO.pot', Path(workdir)/'CuCHO.pot')
        # 队列占据
        hpc = HPCTask(workdir=workdir)
        hpc.scriptdir = '/data/bin/remote.job'
        hpc.connect(target_host, jump_host)
        stdin, stdout, stderr = hpc.ssh_client.exec_command('hostname')
        hostname = stdout.read().decode().strip()
        print(hostname)
        stdin, stdout, stderr = hpc.prerun()
        print(stdout.read().decode().strip())
        print(f"Job {hpc.jobid} status: {hpc.status}")
        jobid = hpc.jobid
        hpc.close()
        # 结构、计算参数设置
        atoms = ase.Atoms('CO', positions=[(0., 0., 0.), (1.2, 0., 0.)], cell=[10, 10, 10], pbc=True)

        # calc 设置
        hpc = HPCTask(workdir=workdir, jobid=jobid)  # reconnect
        hpc.connect(target_host, jump_host)
        calc = hpc_Lasp(
                    command='lasp',
                    directory=workdir,
                    hpctask=hpc,  # 这个非常关键
                    )
        # 计算
        atoms.calc = calc
        e = atoms.get_potential_energy()
        print(f"Energy of CO is {e} eV.")
        # finish job
        hpc.postrun()
        hpc.close()
