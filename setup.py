from setuptools import setup, find_packages


setup(
    name="pkg-deps",
    version=0.1,
    packages=find_packages(),
    install_requires=['pydot3k', 'networkx'],
    entry_points={
        'console_scripts': [
            'pkg_deps = pkg_deps.main:main',
        ],
    },
)
