import logging
import sys

from pathlib import Path

from fabric import task
from invoke import Context

from .config import load_config
from .connection import get_connection
from .runner import (
    _ensure_can_load_data,
    _get_backup_filename,
    _get_media_tar_filename,
    _q,
    _remote_runner,
    _run_safe,
    _split_media_path,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(h)
logger.propagate = False

COMPOSE_CMD = "docker compose exec -T {container} /bin/sh -c '{command}'"
BACKUP_LOCAL_DATA_PATH = Path("./data/")
MEDIA_LOCAL_DIR = Path("./media/")


def _build_pg_dump_cmd(cfg: dict) -> str:
    db = cfg.get("db") or {}
    name = db.get("name")
    user = db.get("user")
    password = db.get("password")
    host = db.get("host", "127.0.0.1")
    port = db.get("port", 5432)

    if not name or not user:
        raise RuntimeError("Missing cfg['db']['name'] or cfg['db']['user'] for bare pg_dump.")

    env_prefix = ""
    if password:
        env_prefix = f"PGPASSWORD={_q(password)} "

    return (
        f"{env_prefix}pg_dump "
        f"-h {_q(host)} -p {_q(port)} -U {_q(user)} "
        f"--no-owner --no-privileges --exclude-schema=postgis "
        f"-Fc -b {_q(name)}"
    )


@task
def download_data(c, env):
    """
    Dump remote data and download it + media files (see params in fab-vars.json)
    """
    cfg = load_config(env)
    copy_cfg = cfg.get("copy_data", {})
    include_db = copy_cfg.get("include_db", True)
    include_media = copy_cfg.get("include_media", False)

    remote_type = cfg.get("remote_type", "docker")
    remote_dir = cfg["remote_dir"]
    media_path = (
        copy_cfg.get("docker_media_path", "/assets/media")
        if remote_type == "docker"
        else copy_cfg.get("media_path")
    )

    run_as = cfg.get("run_as") if remote_type == "docker" else None
    conn = get_connection(cfg, needs_sudo=bool(run_as))
    r_run = _remote_runner(conn, cfg, compose_cmd=COMPOSE_CMD)

    # --- Dump DB ---
    if include_db:
        backup_file = _get_backup_filename(env)
        remote_backup_file = Path("/tmp") / backup_file
        local_backup_file = BACKUP_LOCAL_DATA_PATH / backup_file

        logger.info(f"🗄️  Dump remote database → {backup_file}")

        try:
            if remote_type == "docker":
                cmd = (
                    COMPOSE_CMD.format(
                        container="db",
                        command=(
                            "pg_dump --no-owner --no-privileges --exclude-schema=postgis -Fc -b"
                        ),
                    )
                    + f" > {_q(remote_backup_file)}"
                )
                _run_safe(conn, cmd, cwd=remote_dir, run_as=run_as, desc="pg_dump (docker)")
            else:
                dump_cmd = _build_pg_dump_cmd(cfg) + f" > {_q(remote_backup_file)}"
                r_run(command=dump_cmd, desc="pg_dump (bare)")

            BACKUP_LOCAL_DATA_PATH.mkdir(parents=True, exist_ok=True)
            logger.info(f"⬇️  Download dump to {local_backup_file}")
            conn.get(str(remote_backup_file), str(local_backup_file))
        finally:
            logger.info(f"🧹 Remove temporary dump {remote_backup_file} on server")
            _run_safe(
                conn,
                f"rm {_q(remote_backup_file)}",
                cwd=remote_dir,
                run_as=run_as,
                desc="remove temporary dump",
            )
    else:
        logger.info("⏭️  Database dump ignored (include_db=false)")

    # --- Dump Media files ---
    if include_media:
        if not media_path:
            raise RuntimeError("include_media=true but no media_path configured for bare mode.")

        media_tar = _get_media_tar_filename(env)
        remote_media_tar = Path("/tmp") / media_tar
        local_media_tar = BACKUP_LOCAL_DATA_PATH / media_tar

        parent_dir, base_name = _split_media_path(media_path)
        logger.info(f"🖼️  Archive media files from {media_path}")

        try:
            if remote_type == "docker":
                _run_safe(
                    conn,
                    COMPOSE_CMD.format(
                        container="web", command=f"set -e; test -d {_q(media_path)}"
                    ),
                    cwd=remote_dir,
                    run_as=run_as,
                    desc="check media dir (docker)",
                )
                _run_safe(
                    conn,
                    COMPOSE_CMD.format(
                        container="web",
                        command=f"set -e; tar -C {_q(parent_dir)} -cf - {_q(base_name)}",
                    )
                    + f" > {_q(remote_media_tar)}",
                    cwd=remote_dir,
                    run_as=run_as,
                    desc="tar media (docker)",
                )
            else:
                r_run(command=f"set -e; test -d {_q(media_path)}", desc="check media dir (bare)")
                r_run(
                    command=(
                        "set -e; "
                        f"tar -C {_q(parent_dir)} -cf - {_q(base_name)} > {_q(remote_media_tar)}"
                    ),
                    desc="tar media (bare)",
                )

            _run_safe(
                conn,
                f"test -s {_q(remote_media_tar)}",
                cwd=remote_dir,
                run_as=run_as,
                desc="check non-empty tar",
            )

            BACKUP_LOCAL_DATA_PATH.mkdir(parents=True, exist_ok=True)
            logger.info(f"⬇️  Download media files → {local_media_tar}")
            conn.get(str(remote_media_tar), str(local_media_tar))
        finally:
            logger.info(f"🧹 Remove remote archive {remote_media_tar}")
            _run_safe(
                conn,
                f"rm {_q(remote_media_tar)}",
                cwd=remote_dir,
                run_as=run_as,
                desc="remove temporary media tar",
            )
    else:
        logger.info("⏭️  Media files ignored (include_media=false)")


@task
def upload_data(c, env, env_src=None):
    """
    Upload local data to the remote environment without loading it.
    """
    cfg = load_config(env)
    copy_cfg = cfg.get("copy_data", {})
    include_db = copy_cfg.get("include_db", True)
    include_media = copy_cfg.get("include_media", False)

    env_src = env_src or env

    conn = get_connection(cfg)

    BACKUP_LOCAL_DATA_PATH.mkdir(parents=True, exist_ok=True)

    # --- Upload DB ---
    if include_db:
        backup_name = _get_backup_filename(env_src)
        local_backup_file = BACKUP_LOCAL_DATA_PATH / backup_name
        if not local_backup_file.exists():
            logger.warning(f"⚠️  Dump DB not available: {local_backup_file}. DB step ignored.")
        else:
            remote_backup_file = Path("/tmp") / backup_name
            logger.info(f"⬆️  Upload dump DB → {cfg['host']}:{remote_backup_file}")
            # TODO put with run_as??
            conn.put(str(local_backup_file), str(remote_backup_file))
    else:
        logger.info("⏭️  Upload DB ignored (include_db=false)")

    # --- Upload Media files ---
    if include_media:
        media_tar_name = _get_media_tar_filename(env_src)
        local_media_tar = BACKUP_LOCAL_DATA_PATH / media_tar_name

        if not local_media_tar.exists():
            logger.warning(
                f"⚠️  Media archive not available: {local_media_tar}. Media step ignored."
            )
        else:
            remote_media_tar = Path("/tmp") / media_tar_name
            logger.info(f"⬆️  Upload media files → {cfg['host']}:{remote_media_tar}")
            # TODO put with run_as??
            conn.put(str(local_media_tar), str(remote_media_tar))
    else:
        logger.info("⏭️  Upload media files ignored (include_media=false)")

    logger.info(f"✅ upload_data done for env='{env}' (env_src='{env_src}')")


@task
def load_data(c, env, env_src=None):
    """
    Loads data about the remote environment from /tmp/<env_src>.*
    Requires the .SAFE_TO_OVERWRITE_DB file in remote_dir.

    Note: currently works only in "docker" remote_type.
    """
    cfg = load_config(env)
    remote_type = cfg.get("remote_type", "docker")
    if remote_type != "docker":
        raise RuntimeError("load_data currently supports only remote_type='docker'.")

    remote_dir = cfg["remote_dir"]
    copy_cfg = cfg.get("copy_data", {})
    include_db = copy_cfg.get("include_db", True)
    include_media = copy_cfg.get("include_media", False)
    media_path = copy_cfg.get("docker_media_path", "/assets/media")

    env_src = env_src or env

    run_as = cfg.get("run_as") if remote_type == "docker" else None
    conn = get_connection(cfg, needs_sudo=bool(run_as))

    _ensure_can_load_data(conn, remote_dir, env, run_as)

    # --- DB ---
    if include_db:
        backup_name = _get_backup_filename(env_src)
        remote_backup_file = Path("/tmp") / backup_name

        logger.info(f"📥 Import DB on '{env}' from {remote_backup_file} (source={env_src})")

        _run_safe(
            conn, f"test -s {_q(remote_backup_file)}", run_as=run_as, desc="check remote db backup"
        )

        drop_create_cmd = (
            "docker compose exec -T db /bin/sh -c "
            "'dropdb -U ${POSTGRES_USER} --if-exists --force ${POSTGRES_DB} && "
            " createdb -U ${POSTGRES_USER} -O ${POSTGRES_USER} ${POSTGRES_DB}'"
        )
        _run_safe(
            conn, drop_create_cmd, cwd=remote_dir, run_as=run_as, desc="drop/create DB (remote)"
        )

        restore_cmd = (
            "docker compose exec -T db /bin/sh -c "
            "'pg_restore -U ${POSTGRES_USER} -d ${POSTGRES_DB} "
            "--no-owner --no-privileges' "
            f"< {_q(remote_backup_file)} || true"
        )
        _run_safe(conn, restore_cmd, cwd=remote_dir, run_as=run_as, desc="pg_restore (remote)")

        logger.info("✅ Import DB done")
    else:
        logger.info("⏭️  Import DB ignored (include_db=false)")

    # --- Media files ---
    if include_media:
        media_tar_name = _get_media_tar_filename(env_src)
        remote_media_tar = Path("/tmp") / media_tar_name

        logger.info(f"🖼️  Import media files on '{env}' from {remote_media_tar} (source={env_src})")

        _run_safe(
            conn, f"test -s {_q(remote_media_tar)}", run_as=run_as, desc="check remote media tar"
        )

        parent_dir, _base_name = _split_media_path(media_path)

        import_media_cmd = (
            "docker compose exec -T web /bin/sh -c "
            f"'set -e; mkdir -p {_q(parent_dir)}; "
            f"rm -rf {_q(media_path)}; "
            f"tar -C {_q(parent_dir)} -xf -' "
            f"< {_q(remote_media_tar)}"
        )
        _run_safe(
            conn,
            import_media_cmd,
            cwd=remote_dir,
            run_as=run_as,
            desc="import media files (remote)",
        )

        logger.info("✅ Import media done")
    else:
        logger.info("⏭️  Import media ignored (include_media=false)")

    logger.info(f"✅ load_data done for env='{env}' (env_src='{env_src}')")


@task
def docker_dev_import_data(c, env):
    """
    Import data in dev (docker compose) regarding values in .fab-vars.json
    """
    cfg = load_config(env)
    copy_cfg = cfg.get("copy_data", {})
    include_db = copy_cfg.get("include_db", True)
    include_media = copy_cfg.get("include_media", False)
    create_admin_user = copy_cfg.get("create_admin_user_in_docker_dev", True)

    local = Context()

    if include_db:
        backup_file = BACKUP_LOCAL_DATA_PATH / _get_backup_filename(env)
        if not backup_file.exists():
            logger.warning(f"⚠️  Dump DB not available: {backup_file}. DB step ignored.")
        else:
            logger.info("📥 Import DB in dev : Start")

            _run_safe(
                local,
                "docker compose exec -T db /bin/sh -c "
                "'dropdb -U ${POSTGRES_USER} --if-exists --force ${POSTGRES_DB} && "
                " createdb -U ${POSTGRES_USER} -O ${POSTGRES_USER} ${POSTGRES_DB}'",
                desc="drop/create DB (local docker)",
            )

            _run_safe(
                local,
                "docker compose exec -T db /bin/sh -c "
                f"'pg_restore -U ${{POSTGRES_USER}} -d ${{POSTGRES_DB}} "
                f'--no-owner --no-privileges "/data/{_get_backup_filename(env)}" || true\'',
                desc="pg_restore (local docker)",
            )

            logger.info("📥 Import DB in dev : End")

            if create_admin_user:
                logger.info("👤 Create superuser : Start (admin@example.com / pass=admin)")
                _run_safe(
                    local,
                    COMPOSE_CMD.format(
                        container="web",
                        command=(
                            "DJANGO_SUPERUSER_PASSWORD=admin "
                            "DJANGO_SUPERUSER_EMAIL=admin@example.com "
                            "python3 ./manage.py createsuperuser --no-input || true"
                        ),
                    ),
                )
                logger.info("👤 Create superuser : End")
    else:
        logger.info("⏭️  Import DB ignored (include_db=false)")

    if include_media:
        media_tar = BACKUP_LOCAL_DATA_PATH / _get_media_tar_filename(env)
        if not media_tar.exists():
            logger.warning(f"⚠️  Media archive not available: {media_tar}. Media step ignored.")
        else:
            MEDIA_LOCAL_DIR.mkdir(parents=True, exist_ok=True)
            logger.info(f"🖼️  Extract media files → {MEDIA_LOCAL_DIR}")
            _run_safe(
                local,
                f"tar -xf {media_tar} -C {MEDIA_LOCAL_DIR} --strip-components=1",
                desc="extract media (local)",
            )
            logger.info("🖼️  Import media files : End")
    else:
        logger.info("⏭️  Import media files ignored (include_media=false)")
