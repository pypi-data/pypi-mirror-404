from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
from distutils.errors import CCompilerError, DistutilsExecError, DistutilsPlatformError
from Cython.Build import cythonize
import numpy as np

with open("README.md","r", encoding = 'utf-8') as fp:
    readme = fp.read()

# Define the Cython extensions
extensions = [

    Extension(
        name = "gmms.CampbellBozorgnia2010_cy",
        sources = [ "gmms/CampbellBozorgnia2010_cy.pyx",
        ],
        include_dirs = [np.get_include()],
    ),

    Extension(
        name = "gmms.CampbellBozorgnia2011_cy",
        sources = [ "gmms/CampbellBozorgnia2011_cy.pyx",
        ],
        include_dirs = [np.get_include()],
    ),

    Extension(
        name = "gmms.CampbellBozorgnia2014_cy",
        sources = [ "gmms/CampbellBozorgnia2014_cy.pyx",
        ],
        include_dirs = [np.get_include()],
    ),

    Extension(
        name = "gmms.CampbellBozorgnia2019_cy",
        sources = [ "gmms/CampbellBozorgnia2019_cy.pyx",
        ],
        include_dirs = [np.get_include()],
    ),

    Extension(
        name = "gmms.FoulserPiggottGoda2015_cy",
        sources = [ "gmms/FoulserPiggottGoda2015_cy.pyx",
        ],
        include_dirs = [np.get_include()],
    ),
    
        Extension(
        name = "gmms.distancetools_cy",
        sources = [ "gmms/distancetools_cy.pyx",
        ],
        include_dirs = [np.get_include()],
    ),    
]

class OptionalBuildExt(build_ext):

    def run(self):
        try:
            build_ext.run(self)
        except DistutilsPlatformError:
            self.extensions = []

    def build_extension(self, ext):
        try:
            build_ext.build_extension(self, ext)
        except (CCompilerError, DistutilsExecError, DistutilsPlatformError):
            pass
      
# Call setup
setup(
    name="gmms",
    version="0.2.0",
    
    description="Ground motion models and supporting tools.",
    author="A. Renmin Pretell Ductram",
    author_email='rpretell@unr.edu',
    url="https://github.com/RPretellD/gmms",
    
    long_description_content_type="text/markdown",
    long_description=readme,
    
    packages=find_packages(),

    include_package_data=True,
    ext_modules=cythonize(extensions),
    cmdclass={"build_ext": OptionalBuildExt},
    python_requires	= ">=3.7",
)
