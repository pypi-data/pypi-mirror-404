from setuptools import setup, find_packages

setup(
    name="TOPSIS-Dhruv-102303877",   # PyPI name 
    version="0.0.4",
    author="Dhruv Gupta",
    description="TOPSIS implementation using Python",
    packages=find_packages(),        # finds topsis_dhruv_102303877
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis_dhruv_102303877.topsis:main"
        ]
    },
)
