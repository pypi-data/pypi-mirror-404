from setuptools import setup, find_packages

setup(
    name="graffiti-lookup-nyc",
    version="1.0.1",
    description="Query NYC 311 Graffiti Cleanup Requests via CLI and Python API.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Nabil Jamaleddine",
    author_email="me@nabiljamaleddine.com",
    url="https://github.com/njamaleddine/graffiti-lookup-nyc",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "httpx>=0.23,<0.27",
        "beautifulsoup4>=4.9,<5.0"
    ],
    entry_points={
        "console_scripts": [
            "graffiti-lookup-nyc=graffiti_lookup.__main__:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    package_data={
        "": ["*.md"]
    },
)
