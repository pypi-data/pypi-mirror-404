from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="better-git-of-theseus",
    version="0.5.0",
    description="Plot stats on Git repositories with interactive Plotly charts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Erik Bernhardsson",
    author_email="mail@erikbern.com",
    url="https://github.com/onewesong/better-git-of-theseus",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "gitpython",
        "numpy",
        "tqdm",
        "wcmatch",
        "pygments",
        "plotly",
        "streamlit",
        "python-dateutil",
        "scipy",
        "matplotlib"
    ],
    entry_points={
        "console_scripts": [
            "better-git-of-theseus=git_of_theseus.cmd:main",
        ]
    },
)
