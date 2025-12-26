from setuptools import find_packages, setup

setup(
    name="backend",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["**/*"],
    },
    install_requires=[
        "fastapi",
        "uvicorn",
        "langchain",
        "langchain-community", 
        "langgraph",
        "langsmith",
        "pandas",
        "python-multipart",
        "pypdf"
    ],
)
