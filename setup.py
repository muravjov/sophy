from setuptools import Extension, setup

try:
    from Cython.Build import cythonize
except ImportError:
    import warnings

    cython_installed = False
    warnings.warn("Cython not installed, using pre-generated C source file.")
else:
    cython_installed = True


if cython_installed:
    python_source = "sophy.pyx"
else:
    python_source = "sophy.c"
    cythonize = lambda obj: [obj]

library_source = "src/sophia.c"

sophy = Extension(
    "sophy",
    # extra_compile_args=['-g', '-O0'],
    # :KLUDGE: we don't want to fix sophia.c line (errs in macos),
    # better to update to the latest sophia sources:
    # t->id = id++;
    extra_compile_args=["-Wno-error=int-conversion"],
    # extra_link_args=['-g'],
    sources=[python_source, library_source],
)

setup(
    name="sophy",
    version="0.1.6",
    description="Python bindings for the sophia database.",
    author="Charles Leifer",
    author_email="",
    ext_modules=cythonize(sophy),
)
