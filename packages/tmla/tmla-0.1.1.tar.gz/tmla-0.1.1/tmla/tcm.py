"""TCM model loader from the LIC_TCM repository.

TCM (Transformer-CNN Mixture) is the compression model from
https://github.com/jmliu206/LIC_TCM. It is not shipped with tmla;
run `python init.py` to clone LIC_TCM and download weights.
"""

import sys
from pathlib import Path

# Project root: parent of tmla package
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_LIC_TCM_ROOT = _PROJECT_ROOT / "LIC_TCM"


def get_lic_tcm_path() -> Path:
    """Return the path to the LIC_TCM repository (cloned by init.py)."""
    return _LIC_TCM_ROOT


def _ensure_lic_tcm_on_path() -> None:
    """Add LIC_TCM to sys.path so models.tcm can be imported."""
    lic_tcm = str(_LIC_TCM_ROOT)
    if _LIC_TCM_ROOT.exists():
        if lic_tcm not in sys.path:
            sys.path.insert(0, lic_tcm)
    else:
        raise FileNotFoundError(
            "LIC_TCM repository not found. Run 'python init.py' to clone "
            "https://github.com/jmliu206/LIC_TCM and download weights."
        )


def __getattr__(name: str):
    """Lazy import of TCM from LIC_TCM (models/tcm.py or tcm.py)."""
    if name == "TCM":
        _ensure_lic_tcm_on_path()
        try:
            from models.tcm import TCM  # noqa: PLC0415
        except ImportError:
            from tcm import TCM  # noqa: PLC0415  # LIC_TCM/tcm.py at root
        this = sys.modules[__name__]
        setattr(this, "TCM", TCM)
        return TCM
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return ["TCM", "get_lic_tcm_path"]


__all__ = ["TCM", "get_lic_tcm_path"]
