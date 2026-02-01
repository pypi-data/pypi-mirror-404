import os
import posixpath
import shlex
import sys
import uuid

from pathlib import Path

from fabric import Connection
from invoke.exceptions import UnexpectedExit


def _q(s) -> str:
    """Shell-quote a single token (path, arg, etc.)."""
    return shlex.quote(str(s))


def _is_sudo_password_set(conn: Connection) -> bool:
    return bool(conn.config.sudo.get("password"))


def _run_safe(
    actor,
    cmd: str,
    *,
    cwd: str | None = None,
    run_as: str | None = None,
    hide: bool = True,
    pty: bool = False,
    desc: str | None = None,
):
    """
    Run a shell command (local or remote) while preventing sensitive stdout/stderr
    from leaking on failure.

    If run_as is provided:
      - remote only (fabric.Connection)
      - requires sudo password configured on the Connection (conn.config.sudo.password)
      - uses sudo + su to switch to that user
    """
    is_remote = isinstance(actor, Connection)

    if cwd:
        cmd = f"cd {_q(cwd)} && {cmd}"

    try:
        if run_as:
            if not is_remote:
                raise RuntimeError("run_as is only supported for remote Connection.")
            if not _is_sudo_password_set(actor):
                raise RuntimeError("run_as requires sudo_password to be set in fabric config.")

            # Run command as another user via root sudo + su -c
            cmd = f"su {run_as} -c {_q(cmd)}"
            return actor.sudo(cmd, hide=hide, pty=True)

        return actor.run(cmd, hide=hide, pty=pty)

    except UnexpectedExit as e:
        role = "Remote" if is_remote else "Local"
        code = getattr(e.result, "exited", None)
        msg = f"{role} command failed"
        if code is not None:
            msg += f" (exit={code})"
        if desc:
            msg += f": {desc}"
        raise RuntimeError(msg) from e


def upload_with_progress(
    conn: Connection,
    local_path: str,
    remote_path: str,
    run_as: str | None = None,
):
    """
    Upload `local_path` -> `remote_path` with progress bar.
    If run_as is provided, upload to a temp file then sudo-move.
    """
    sftp = conn.sftp()
    bar_width = 30

    local_size = os.path.getsize(local_path)

    # where to upload initially
    remote_tmp = f"/tmp/{uuid.uuid4().hex}" if run_as else remote_path

    def _print_progress(transferred, total):
        total = total or local_size
        percent = int(transferred * 100 / total)
        filled = int(bar_width * percent / 100)
        bar = "█" * filled + "." * (bar_width - filled)
        mb_transferred = transferred / 1_000_000
        mb_total = total / 1_000_000

        sys.stdout.write(f"\r   [{bar}] {percent:3d}% ({mb_transferred:6.1f}/{mb_total:6.1f} MB)")
        sys.stdout.flush()

        if transferred >= total:
            sys.stdout.write("\n")

    sftp.put(local_path, remote_tmp, callback=_print_progress)

    if run_as:
        remote_dir = posixpath.dirname(remote_path)

        conn.sudo(f"mkdir -p {remote_dir}", user=run_as)
        conn.sudo(f"mv {remote_tmp} {remote_path}")
        conn.sudo(f"chown {run_as}:{run_as} {remote_path}")


# --- data-related helpers (MISSING BEFORE; used by data.py imports) ---


def _get_backup_filename(env: str) -> str:
    return f"{env}.backup"


def _get_media_tar_filename(env: str) -> str:
    return f"{env}.media.tar"


def _split_media_path(path_str: str):
    """
    Return (parent_dir, base_name)
    Ex: '/assets/media/' -> ('/assets', 'media') ; '/src/media' -> ('/src', 'media')
    """
    if not path_str.startswith("/"):
        raise ValueError(f"media_path must be absolute (received: {path_str!r})")

    path = Path(path_str.rstrip("/"))
    return str(path.parent), path.name


def _ensure_can_load_data(conn: Connection, remote_dir: str, env: str, run_as: str | None = None):
    """
    Check safeguard for remote destructive load.

    Conditions:
      - `.SAFE_TO_OVERWRITE_DB` file present in remote_dir
      - If the environment name resembles prod, log a major WARNING
    """
    allow_file = Path(remote_dir) / ".SAFE_TO_OVERWRITE_DB"

    if "prod" in env.lower():
        raise RuntimeError("Not possible to run fab load_data on production environment.")

    result = _run_safe(
        conn, f"test -f {_q(allow_file)}", run_as=run_as, desc="check can load data"
    )
    if result.exited != 0:
        raise RuntimeError(
            "Data loading DENIED.\n"
            f"The safeguard file {allow_file} cannot be found on the server.\n"
            "Create this file manually on the server to authorize the command "
            "`fab load_data ...`."
        )


def _remote_runner(conn: Connection, cfg: dict, *, compose_cmd: str):
    """
    Return a callable: run(container=None, command="...") -> Result
    - docker: executes command inside container via docker compose exec
    - bare: executes command directly on host
    """
    remote_type = cfg.get("remote_type", "docker")

    if remote_type == "docker":
        remote_dir = cfg["remote_dir"]
        compose_prefix = f"cd {remote_dir} && {compose_cmd}"

        def run(*, container, command, hide=True, pty=False, desc=None):
            full = compose_prefix.format(container=container, command=command)
            return _run_safe(conn, full, hide=hide, pty=pty, desc=desc)

        return run

    if remote_type == "bare":

        def run(*, container=None, command="", hide=True, pty=False, desc=None):
            return _run_safe(conn, command, hide=hide, pty=pty, desc=desc)

        return run

    raise ValueError(f"Unknown remote_type={remote_type!r}")
