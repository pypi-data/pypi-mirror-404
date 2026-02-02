from setuptools import setup

with open("README.md", "r", encoding='utf-8') as f:
    long_description = f.read()

install_requires = [
    'ase',
    'paramiko',
]

setup(
    name='hpc_task',
    version='0.1.1',
    packages=['hpc_task'],
    url='https://gitee.com/pjren/hpc_task',
    license='MIT',
    author='Renpj',
    author_email='0403114076@163.com',
    description='HPC Task python library.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
