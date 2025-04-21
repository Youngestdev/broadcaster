from setuptools import setup, find_packages

setup(
    name="broadcaster",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pymongo>=4.0",
        "motor>=3.0",
        "pydantic>=2.0",
        "aiohttp>=3.8",
        "redis>=5.2.1",
        "tenacity>=9.1.2"
    ],
    extras_require={
        "fastapi": ["fastapi>=0.95.0", "sse-starlette>=1.0.0"],
    },
    python_requires=">=3.8",
    author="Abdulazeez Abdulazeez Adeshina",
    author_email="youngestdev@gmail.com",
    description="A package to broadcast MongoDB change streams to various channels",
    license="MIT",
    keywords="mongodb change stream websocket redis http",
)
