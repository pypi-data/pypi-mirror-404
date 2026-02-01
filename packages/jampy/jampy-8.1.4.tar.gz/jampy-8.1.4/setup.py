from setuptools import setup, find_packages
import re

package = "jampy"

def find_version():
    version_file = open(package + "/__init__.py").read()
    rex = r'__version__\s*=\s*"([^"]+)"'
    return re.search(rex, version_file).group(1)

def read_docstring(name, file=None):
    """
    name: 
        Class/function name from which to extract the docstring.
    file: 
        Name of the file containing the class/function, relative to the package
        directory. If file is None, it is assumed to be: package + '/name.py'
    """
    if file is None:
        file = name + ".py"
    main_file = open(package + "/" + file).read()
    rex = rf'(?:def {name}[\s\S]+?|class {name}):\n\s*"""([\s\S]+?)"""'
    docstring = re.search(rex, main_file).group(1)
    return docstring.replace("\n    ", "\n")

setup(name=package,
      version=find_version(),
      description="JamPy: Jeans Anisotropic Models for Galactic Dynamics",
      long_description_content_type='text/x-rst',
      long_description=open(package + "/README.rst").read()
                       + read_docstring("jam_axi_proj", "axi/jam_axi_proj.py")
                       + read_docstring("jam_axi_intr", "axi/jam_axi_intr.py")
                       + open(package + "/LICENSE.txt").read()
                       + open(package + "/CHANGELOG.rst").read(),
      url="https://purl.org/cappellari/software",
      author="Michele Cappellari",
      author_email="michele.cappellari@physics.ox.ac.uk",
      license="Other/Proprietary License",
      packages=find_packages(),
      package_data={package: ["*.rst", "*.txt", "*/*.txt"]},
      install_requires=["numpy", "scipy", "matplotlib", "plotbin"],
      classifiers=["Development Status :: 5 - Production/Stable",
                   "Intended Audience :: Developers",
                   "Intended Audience :: Science/Research",
                   "Operating System :: OS Independent",
                   "Programming Language :: Python :: 3"],
      zip_safe=True)
