from setuptools import setup, find_packages

setup(
    name="topsis-rhythm-102303707",
    version="1.0.0",
    author="Rhythm Ghai",
    description="TOPSIS Multi-Criteria Decision Making Tool with CLI Support",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy"
    ],
    entry_points={
        "console_scripts": [
            "topsis=topsis_rhythm_102303707.cli:main"
        ]
    }
)

