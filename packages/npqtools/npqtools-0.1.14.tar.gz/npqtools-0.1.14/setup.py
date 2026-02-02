from setuptools import setup, find_packages

setup(
    name='npqtools',
    version='0.1.14',
    author='Mikhail Tseytlin',
    author_email='tseytlinmikhail@gmail.com',
    description='Library for reinterpretation main np-problems into Ising model for quantum computer',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://gitverse.ru/mits2406/npqtools',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
    install_requires=[
        'numpy>=2.0.2',
        'matplotlib>=3.9.2',
        'dimod>=0.12.18',
        'dwave-samplers>=1.4.0',
    ],
)