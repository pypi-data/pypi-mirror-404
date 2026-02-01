"""Wrapper for fTetWild."""


# start delvewheel patch
def _delvewheel_patch_1_12_0():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'pytetwild.libs'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_12_0()
del _delvewheel_patch_1_12_0
# end delvewheel patch

from ._version import __version__  # noqa: F401
from .pytetwild import tetrahedralize, tetrahedralize_pv, tetrahedralize_csg  # noqa: F401
