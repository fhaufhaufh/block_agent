from setuptools import setup, find_packages
from catkin_pkg.python_setup import generate_distutils_setup

d = generate_distutils_setup(
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'langgraph>=0.2.0',
        'langchain>=0.3.0',
        'langchain-openai>=0.2.0',
        'pydantic>=2.0.0',
        'python-dotenv>=1.0.0',
    ],
)

setup(**d)