"""
Setup configuration for visor_vari package.

"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="visor_vari",
    version="1.8",
    author="El señor es el único eterno. Que la ciencia lo honre a Él",
    author_email="from.colombia.to.all@gmail.com",
    description="Permite la visualización de grandes conjuntos de datos en sistemas (software) complejos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Metal-Alcyone-zero/visor_vari",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Debuggers",
    ],
    python_requires=">=3.6",
    install_requires=[
        # tkinter viene incluido con Python
        "# No es necesario instalarlo por separado"
    ]
)
