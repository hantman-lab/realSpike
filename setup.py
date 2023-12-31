from setuptools import setup, find_packages
from pathlib import Path

install_requires = [
    "numpy",
    "fastplotlib",
    "ipywidgets",
    "pytest",
    "glfw",
    "tqdm",
    "requests",
    "jupyter-rfb",
    "jupyterlab<4",
    "jupyterlab-widgets",
    "improv"
]

with open(Path(__file__).parent.joinpath("README.md")) as f:
    readme = f.read()

with open(Path(__file__).parent.joinpath("real_spike", "VERSION"), "r") as f:
    ver = f.read().split("\n")[0]

setup(
    name='realSpike',
    version=ver,
    long_description=readme,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    url='https://github.com/hantman-lab/realSpike',
    license='GPL-3.0 license',
    author='clewis7',
    author_email='',
    python_requires='>=3.8,<3.11',
    install_requires=install_requires,
    extras_require=None,
    include_package_data=True,
    description='Real-time ephys visualization and analysis tool'
)