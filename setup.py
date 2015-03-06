from setuptools import setup, find_packages


setup(
    name="pkg-deps",
    version=0.2,
    packages=find_packages(),
    install_requires=['pydot3k', 'networkx', 'click'],
    # entry_points based script is really slow (0.5 seconds)
    # might want to switch to normal script, since windows
    # version isn't a concern right now
    entry_points={
        'console_scripts': [
            'pkg_deps = pkg_deps.main:main',
        ],
    },
)
