from setuptools import setup, find_packages

setup(
    name="topsis-sneha-102303723",
    version="1.0.0",
    author="Sneha",
    author_email="ssneha1_be23@thapar.edu",
    description="TOPSIS implementation using Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=["pandas", "numpy"],
    entry_points={
        "console_scripts": [
            "topsis=topsis.topsis:main"
        ]
    },
)
