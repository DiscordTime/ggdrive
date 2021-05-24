import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = fh.read().splitlines()

setuptools.setup(
    name='ggdrive',
    version='0.1.4',
    scripts=['gdrive'],
    author="DiscordTime",
    description="A command-line tool for operating on Google Drive directly from the terminal.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DiscordTime/ggdrive",
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
)
