"""LibreOffice (soffice) helpers for document conversion.

Provides environment setup and execution helpers for running soffice
in headless mode, including a shim for macOS to avoid display issues.
"""

import ctypes
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_SHIM_SOURCE = r"""
#include <dlfcn.h>
#include <stdlib.h>

/* Shim to prevent soffice from trying to connect to a display on macOS.
   Load this with DYLD_INSERT_LIBRARIES to intercept display-related calls. */

static void* _get_sym(const char* lib, const char* sym) {
    void* handle = dlopen(lib, RTLD_LAZY | RTLD_NOLOAD);
    if (!handle) return NULL;
    return dlsym(handle, sym);
}

/* Intercept NSApplicationMain to prevent GUI startup */
int NSApplicationMain(int argc, const char* argv[]) {
    (void)argc; (void)argv;
    return 0;
}
"""

_shim_path: Path | None = None


def get_soffice_env() -> dict[str, str]:
    """Return an environment dict suitable for running soffice headlessly."""
    env = os.environ.copy()

    # Unset display variables to force headless mode
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)

    # Set a writable user installation directory to avoid conflicts
    user_install = Path(tempfile.gettempdir()) / "soffice_userinstall"
    user_install.mkdir(exist_ok=True)
    env["UserInstallation"] = f"file://{user_install}"

    if sys.platform == "darwin" and _needs_shim():
        shim = _ensure_shim()
        if shim:
            existing = env.get("DYLD_INSERT_LIBRARIES", "")
            if existing:
                env["DYLD_INSERT_LIBRARIES"] = f"{shim}:{existing}"
            else:
                env["DYLD_INSERT_LIBRARIES"] = str(shim)

    return env


def run_soffice(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run soffice with the correct headless environment.

    Args:
        args: Arguments to pass to soffice (without the 'soffice' prefix).
        **kwargs: Additional arguments forwarded to subprocess.run.

    Returns:
        CompletedProcess instance.
    """
    cmd = ["soffice", "--headless"] + args
    env = get_soffice_env()
    return subprocess.run(cmd, env=env, capture_output=True, text=True, **kwargs)


def _needs_shim() -> bool:
    """Check if we need the macOS display shim."""
    if sys.platform != "darwin":
        return False
    # Check if we're in a headless environment (no DISPLAY, no active window server)
    try:
        result = subprocess.run(
            ["defaults", "read", "com.apple.windowserver", "DisplayResolutionEnabled"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.returncode != 0
    except Exception:
        return False


def _ensure_shim() -> Path | None:
    """Compile and cache the macOS display shim dylib.

    Returns:
        Path to the compiled shim, or None if compilation failed.
    """
    global _shim_path

    if _shim_path is not None and _shim_path.exists():
        return _shim_path

    shim_dir = Path(tempfile.gettempdir()) / "soffice_shim"
    shim_dir.mkdir(exist_ok=True)
    shim_so = shim_dir / "soffice_shim.dylib"

    if shim_so.exists():
        _shim_path = shim_so
        return _shim_path

    src_path = shim_dir / "soffice_shim.c"
    src_path.write_text(_SHIM_SOURCE, encoding="utf-8")

    try:
        result = subprocess.run(
            [
                "cc",
                "-dynamiclib",
                "-o",
                str(shim_so),
                str(src_path),
                "-framework",
                "CoreFoundation",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and shim_so.exists():
            _shim_path = shim_so
            return _shim_path
    except Exception:
        pass

    return None
