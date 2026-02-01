from setuptools import setup, find_packages

setup(
    name="KickZero",
    version="1.1.0",
    author="Seymen Sözen",
    description="Kick.com için gelişmiş ve kolay kullanımlı bot framework'ü",
    long_description=open("README.md", encoding="utf-8").read(), # Buraya encoding="utf-8" ekledik
    long_description_content_type="text/markdown",
    url="https://github.com/SeymenSozen/KickZero",
    packages=find_packages(),
    install_requires=[
        "aiohttp",
        "websockets",
        "colorama",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)