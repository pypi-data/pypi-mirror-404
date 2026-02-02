import os
import re
from pathlib import Path
from time import sleep

from paramiko import SSHClient, SSHException, AutoAddPolicy
from .templates import QSUB, QDEL, QSTAT, CWD
from stat import S_ISDIR


class HPCTask:
    scriptdir = '$HOME/bin/remote_job.sh'  # 排队系统脚本默认名称

    def __init__(self, workdir=None, jobid=None):
        # TODO：支持不包含 gosh-remote 的情况
        self._hostname = None
        self._qtype = None
        self._ssh_jump = None
        self.jobid = None
        if jobid is not None:
            self.jobid = jobid
            # TODO：self.workdir = self.get_workdir(jobid)
        self.ssh_client = None
        self.workdir = workdir
        self._need_sync = None
        self._remote_parent_workdir = None

    @property
    def _script_name(self):
        return self.scriptdir.split('/')[-1]

    def connect(self, target_host, jump_host=None):
        """
        开启队列
        :return: jobid
        """
        # 建立 ssh 连接
        # 跳板机连接信息
        if self.ssh_client is None:
            try:
                # 使用隧道连接到目标服务器
                target_client = SSHClient()
                target_client.set_missing_host_key_policy(AutoAddPolicy())
                # 首先连接到跳板机
                if jump_host is not None:
                    # 创建SSH客户端
                    jump_client = SSHClient()
                    jump_client.set_missing_host_key_policy(AutoAddPolicy())
                    jump_client.connect(**jump_host)
                    # 在跳板机上创建到目标服务器的隧道
                    transport = jump_client.get_transport()
                    dest_addr = (target_host['hostname'], target_host['port'])
                    local_addr = ('127.0.0.1', 0)  # 本地任意端口
                    channel = transport.open_channel('direct-tcpip', dest_addr, local_addr)
                    target_client.connect('127.0.0.1',
                                          port=channel.getpeername()[1],
                                          username=target_host['username'],
                                          password=target_host['password'],
                                          sock=channel)
                    self._ssh_jump = jump_client
                else:
                    target_client.connect(**target_host)

                self.ssh_client = target_client
                print(f"Connect to SSH Server {self.hostname} success, job scheduling system is {self.qtype}.")
            except SSHException as e:
                raise e

            # get remote parent workdir
            command = 'pwd'
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            self._remote_parent_workdir = stdout.read().decode('utf-8').strip().split()[-1]

    def get_workdir(self):
        # TODO: 需要测试 LSF、和 PBS
        if self.jobid is not None:
            command = f"{CWD[self.qtype].format(jobid=self.jobid)}"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            abs_workdir = stdout.read().decode('utf-8').strip().split()[-1]
            workdir = Path(abs_workdir).relative_to(Path(self._remote_parent_workdir))
            if self.workdir is None:
                self.workdir = str(workdir)
        return self.workdir

    @property
    def need_sync(self):  # 检查是否需要同步数据
        if self._need_sync is None:
            # 通过检查本地是否存在 workdir/script_name
            local_file = Path(self.workdir) / self._script_name
            self._need_sync = not local_file.exists()
        return self._need_sync

    @need_sync.setter
    def need_sync(self, v):
        self._need_sync = v

    @property
    def qtype(self):
        if self.ssh_client is None:
            raise RuntimeError('ssh client is not connected')
        if self._qtype is None:
            command = ('sinfo 2>/dev/null && echo "slurm" || '
                       '(qstat -q 2>/dev/null && echo "pbs" || '
                       '(bqueues 2>/dev/null && echo "lsf" || '
                       'echo "unknown"))')
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            self._qtype = stdout.read().decode('utf-8').strip().split()[-1]
        if self._qtype is 'unknown':
            raise NotImplementedError('qtype is not implemented')
        return self._qtype

    @property
    def hostname(self):
        if self.ssh_client is None:
            raise RuntimeError('ssh client is not connected')
        if self._hostname is None:
            stdin, stdout, stderr = self.ssh_client.exec_command('hostname')
            self._hostname = stdout.read().decode('utf-8').strip()
        return self._hostname

    def prerun(self):
        # 提交任务，占据节点
        if self.ssh_client is None:
            raise RuntimeError('ssh client is not connected')

        # 判断是否存在 gosh-remote 命令
        command = f"which gosh-remote"
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        if len(stdout.read().decode().strip()) == 0:
            raise RuntimeError(f'gosh-remote command not found on server.')
        # 判断是否存在 HPC_SCRIPT
        command = f'ls {self.scriptdir} > /dev/null && echo "Y" || echo "N"'
        stdin, stdout, stderr = self.ssh_client.exec_command(command)
        if stdout.read().decode().strip() != 'Y':
            raise FileNotFoundError(f'{self.scriptdir} not found on server.')

        commands = [f'[ -d {self.workdir} ] || mkdir -p {self.workdir}',
                    f'cd {self.workdir}',
                    f'cp {self.scriptdir} {self._script_name}']
        stdin, stdout, stderr = self.ssh_client.exec_command(';'.join(commands))
        self.jobid = self.submit()
        return stdin, stdout, stderr

    def postrun(self):
        """
        说明：关闭任务节点占用
        bkill JOBID是从任务头部开始杀, KILL 信号会传递到子进程
        pkill gosh-remote 是直接杀
        二者可能相同, 也可能不相同. 取决于 bsub 时如何定义的.
        通常 bsub 是用一个 script 调 gosh-remote, 这时二者就不同了.
        那个主调script 可能会做信号处理, 会顺着 gosh-remote的调用进程下去, 逐一 KILL.
        gosh-remote我不记得是否有信号处理的逻辑, 得做实验确认一下.

        :return:
        """

        if self.ssh_client is None:
            raise RuntimeError('ssh client is not connected')
        commands = ['sleep 1', f'{QDEL[self.qtype]} {self.jobid}', 'pkill gosh-remote']
        stdin, stdout, stderr = self.ssh_client.exec_command(';'.join(commands))
        return stdin, stdout, stderr

    @property
    def status(self):
        """
        查询作业状态：排队(PEND)，运行(RUN)，结束(DONE), 未知 （UNKNOWN），挂起（SUSPENDED）,未发现（NOT_FOUND）
        :return: status
        """
        if self.ssh_client is None:
            raise RuntimeError('ssh client is not connected')
        stat = "UNKNOWN"
        stdin, stdout, stderr = self.ssh_client.exec_command(f"{QSTAT[self.qtype]} {self.jobid}")
        output = stdout.read().decode()
        if self.qtype == 'slurm':
            # case 1: "slurm_load_jobs error: Invalid job id specified"
            # case 2 (noheader): "RUNNING"
            status_map = {
                "PENDING": "PEND",
                "RUNNING": "RUN",
                "SUSPENDED": "SUSPENDED",
                "COMPLETED": "DONE",
                "COMPLETING": "DONE",
                "REQUEUED": "PEND",
            }
            if "Invalid job id specified" in output:
                stat = "NOT_FOUND"
            else:
                stat = status_map.get(output.strip(), "UNKNOWN")
        elif self.qtype == 'pbs':
            not_found_pattern = r'qstat: Unknown Job Id|qstat: Invalid job id specified'
            job_state_pattern = r'job_state\s*=\s*(\w+)'
            status_map = {
                "Q": "PEND", # Queued
                "W": "PEND", # Waiting
                "T": "PEND", # Transition
                "H": "PEND", # Held
                "R": "RUN",
                "S": "SUSPENDED",
                "C": "DONE", # Completed
                "F": "DONE", # Finished
            }
            if re.search(not_found_pattern, output):
                stat = "NOT_FOUND"
            else:
                match = re.search(job_state_pattern, output)
                if match:
                    status = match.group(1)
                    return status_map.get(status, "UNKNOWN")
                else:
                    stat = "UNKNOWN"
        elif self.qtype == 'lsf':
            # case 1: "688559  renpeng RUN   proj       Khpcserver0 72*Knode44  scheduler  Sep  8 10:55"
            # case 2: "Job <1> is not found"
            patterns = [
                r'Job\s*<.*>\s*is not found',  # 作业不存在
                r'No (.*) job found',  # 另一种不存在提示
                r'(\S+)\s+\S+\s+(\S+)\s+',  # 标准状态格式
                r'JOBID\s+USER\s+STAT\s+',  # 表头检测
            ]
            # 检查作业是否存在
            if re.search(patterns[0], output) or re.search(patterns[1], output):
                stat = "NOT_FOUND"
            lines = output.strip().split('\n')
            for line in lines:
                # 跳过表头
                if re.search(patterns[3], line):
                    continue
                # 匹配状态行
                match = re.search(patterns[2], line)
                if match:
                    status = match.group(2)
                    status_map = {
                        'RUN': 'RUN',
                        'PEND': 'PEND',
                        'DONE': 'DONE',
                        'EXIT': 'DONE',
                        'PSUSP': 'SUSPENDED',
                        'USUSP': 'SUSPENDED',
                        'SSUSP': 'SUSPENDED'
                    }
                    stat = status_map.get(status, "UNKNOWN")
        else:
            raise RuntimeError(f'{self.qtype} is not supported')
        return stat

    def submit(self):
        """
        :return: None
        """
        if self.ssh_client is None:
            raise RuntimeError('ssh client is not connected')
        jobid = None
        script_name = self.scriptdir.split('/')[-1]
        # 必须使用下面的方式提交，否则无法加载.bashrc的环境变量
        stdin, stdout, stderr = self.ssh_client.exec_command(f'''
            bash --login -i << 'EOF'
            cd {self.workdir}
            {QSUB[self.qtype]} {script_name}
            EOF
        ''')
        output = stdout.read().decode().strip()
        if len(output)==0:
            raise RuntimeError(f'{stderr.read().decode().strip()}')

        patterns = [
            r'Job\s*[<\[\(]?\s*(\d+)\s*[>\]\)]?\s*is submitted',  # 标准格式
            r'Submitted\s+batch\s+job\s+(\d+)',  # slurm 格式
            r'(\d+)\s+\.',  # PBS 格式
            r'job\s+["\']?(\d+)["\']?\s+submitted',  # 其他变体
        ]
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                jobid = match.group(1)
        self.jobid = jobid
        return jobid

    def execute(self, command):
        status = self.status
        need_sync = self.need_sync
        if need_sync:
            self.upload()
        while True:
            if status == 'RUN':
                stdin, stdout, stderr = (
                    self.ssh_client.exec_command(f'cd {self.workdir};{command}'))
                output = stdout.read().decode().strip()
                err = stderr.read().decode().strip()
                returncode = 0
                break
            elif status == 'PEND':
                print(f"Waiting for the queue 10 seconds...")
                sleep(10)
                status = self.status
                need_sync = False
            elif status in ('SUSPENDED', 'DONE'):
                output = ''
                err = f"Job {self.jobid} status: {status}"
                returncode = 1
                need_sync = False
                break
            else:
                output = ''
                err = f'{self.qtype} with {status} is not supported'
                returncode = 2
                need_sync = False
                break
        if need_sync:
            self.download()
        return returncode, err, output

    def upload(self):
        """
        TODO: 使用 rsync
        :return: file sync status
        """
        if self.ssh_client is None:
            raise RuntimeError('ssh client is not connected')

        # 创建服务器目录，如果不存在
        self.ssh_client.exec_command(f'if [ ! -d "{self.workdir}" ]; then mkdir -p {self.workdir};fi')
        sftp_client = self.ssh_client.open_sftp()
        local_path = Path(self.workdir)
        remote_path = Path(self.workdir)

        for root, dirs, files in os.walk(local_path):
            rel_path = Path(root).relative_to(local_path)
            remote_dir = remote_path / rel_path
            if str(rel_path) != ".":
                _ensure_remote_dir_exists(sftp_client, str(remote_dir))
            # 上传文件
            for file in files:
                local_file = Path(root) / file
                remote_file = remote_dir / file
                sftp_client.put(str(local_file), str(remote_file), confirm=False)

        return None

    def download(self):
        if self.ssh_client is None:
            raise RuntimeError('ssh client is not connected')

        sftp_client = self.ssh_client.open_sftp()
        _download_dir(sftp_client, remote=self.workdir, local=self.workdir)
        #for filename in sftp_client.listdir(self.workdir):  # TODO: 递归所有文件夹
        #    sftp_client.get(os.path.join(self.workdir,filename), os.path.join(self.workdir,filename))
        sftp_client.close()
        return None

    def close(self):
        """
        关闭队列
        """
        if self.ssh_client is not None:
            self.ssh_client.close()
        if self._ssh_jump is not None:
            self._ssh_jump.close()
        return None


def _ensure_remote_dir_exists(sftp, remote_dir):
    """确保远程目录存在"""
    try:
        sftp.stat(remote_dir)
    except FileNotFoundError:
        # 递归创建目录
        parts = Path(remote_dir).parts
        current_path = parts[0]
        for part in parts[1:]:  # 跳过根目录
            current_path = os.path.join(current_path, part)
            try:
                sftp.stat(current_path)
            except FileNotFoundError:
                sftp.mkdir(current_path)

def _download_dir(sftp, remote, local):
    os.makedirs(local, exist_ok=True)
    for item in sftp.listdir(remote):
        src, dst = f"{remote}/{item}", f"{local}/{item}"
        if S_ISDIR(sftp.stat(src).st_mode):
            _download_dir(sftp, src, dst)
        else:
            sftp.get(src, dst)
