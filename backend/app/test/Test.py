import ntpath
import os
import shutil


def _shell_name(shell: str) -> str:
    """Return the executable name for a shell path or command."""
    return shell.replace("\\", "/").rsplit("/", 1)[-1].lower()



def _find_first_available_shell(candidates: tuple[str, ...]) -> str | None:
    """Return the first executable shell path or command found from candidates."""
    for shell in candidates:
        if os.path.isabs(shell):
            if os.path.isfile(shell) and os.access(shell, os.X_OK):
                return shell
            continue

        shell_from_path = shutil.which(shell)
        if shell_from_path is not None:
            return shell_from_path

def _get_shell() -> str:
    """Detect available shell executable with fallback."""
    shell = _find_first_available_shell(("/bin/zsh", "/bin/bash", "/bin/sh", "sh"))
    print(shell)
    if shell is not None:
        return shell

    print('os.name: ', os.name)

    if os.name == "nt":
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        shell = _find_first_available_shell(
            (
                "pwsh",
                "pwsh.exe",
                "powershell",
                # "powershell.exe",
                # ntpath.join(system_root, "System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
                "cmd.exe",
            )
        )
        if shell is not None:
            return shell

        raise RuntimeError("No suitable shell executable found. Tried /bin/zsh, /bin/bash, /bin/sh, `sh` on PATH, then PowerShell and cmd.exe fallbacks for Windows.")

    raise RuntimeError("No suitable shell executable found. Tried /bin/zsh, /bin/bash, /bin/sh, and `sh` on PATH.")


shell = _get_shell()

print('_shell_name: ', shell)