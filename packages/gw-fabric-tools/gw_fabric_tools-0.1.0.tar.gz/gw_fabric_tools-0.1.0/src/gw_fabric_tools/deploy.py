import logging
import sys

from datetime import datetime

from fabric import task
from invoke import Context

from .config import load_config
from .connection import get_connection
from .runner import _q, _run_safe, upload_with_progress

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    logger.addHandler(h)
logger.propagate = False

COMPOSE_CMD = "docker compose exec -T {container} /bin/sh -c '{command}'"


@task
def deploy(c, env, build_without_cache=False):
    """
    Deploy application depending on remote_type:
    - docker: build locally, upload image tar, docker load, compose restart, migrate
    - bare: git pull, pip install, migrate, collectstatic, compilemessages, restart/touch
    """
    cfg = load_config(env)
    remote_type = cfg.get("remote_type", "docker")
    run_as = cfg.get("run_as")

    if remote_type == "docker":
        _deploy_docker(env, cfg, run_as, build_without_cache=build_without_cache)
        return

    if remote_type == "bare":
        _deploy_bare(cfg, run_as)
        return

    raise ValueError(f"Unknown remote_type={remote_type!r}")


def _deploy_docker(env_name, cfg, run_as, *, build_without_cache=False):
    local = Context()

    remote_dir = cfg["remote_dir"]
    image_name = cfg["web_image_name"]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    image = f"{image_name}:{env_name}"
    tar = f"/tmp/{image_name}_{env_name}_{timestamp}.tar"

    logger.info(f"📦 Build image {image}…")
    cmd = f"WEB_IMAGE={image} docker compose -f docker-compose.yml build web"
    if build_without_cache:
        cmd = f"{cmd} --no-cache"
    local.run(cmd)

    logger.info(f"📤 Export image {image} to {tar}…")
    local.run(f"docker save {image} -o {tar}")

    conn = get_connection(cfg, needs_sudo=bool(run_as))

    logger.info(f"📂 Send image {tar} to server…")
    upload_with_progress(conn, tar, tar, run_as=run_as)

    logger.info(f"📥 Load image {tar} on server…")
    _run_safe(conn, f"docker load -i {_q(tar)}", run_as=run_as, desc="docker load")

    logger.info(f"🧹 Clean {tar} on server")
    _run_safe(conn, f"rm {_q(tar)}", run_as=run_as, desc="remove temporary image tar")
    logger.info(f"🧹 Clean {tar} on local machine")
    local.run(f"rm {_q(tar)}")

    logger.info("🔁 Full restart (down & up)…")
    _run_safe(
        conn,
        "docker compose down --remove-orphans && docker compose up -d",
        run_as=run_as,
        cwd=remote_dir,
        desc="compose restart",
    )

    if (cfg.get("deploy") or {}).get("migrate", True):
        logger.info("🚨 Django migrations…")
        _run_safe(
            conn,
            "docker compose exec -T web python manage.py migrate",
            run_as=run_as,
            cwd=remote_dir,
            desc="migrate db (docker)",
        )


def _deploy_bare(cfg, run_as):
    deploy_cfg = cfg.get("deploy") or {}
    remote_dir = cfg["remote_dir"]

    venv_activate = deploy_cfg["venv_activate"]
    requirements = deploy_cfg.get("requirements")
    settings_module = deploy_cfg.get("settings_module")
    manage_py = deploy_cfg.get("manage_py", "manage.py")

    collectstatic = deploy_cfg.get("collectstatic", True)
    compilemessages = deploy_cfg.get("compilemessages", True)
    touch_paths = deploy_cfg.get("touch_paths", [])

    media_owner = deploy_cfg.get("media_owner")
    media_group = deploy_cfg.get("media_group")
    media_path = deploy_cfg.get("media_path", "media")

    restart_cfg = deploy_cfg.get("restart") or {"type": "touch"}

    conn = get_connection(cfg, needs_sudo=True)

    logger.info(f"🚀 Bare deploy on {cfg['host']} (dir={remote_dir})")

    logger.info("📥 git pull…")
    _run_safe(conn, "git pull", cwd=remote_dir, run_as=run_as, desc="git pull")

    if media_owner and media_group:
        test_cmd = f'test "$(stat -c "%U:%G" {_q(media_path)})" = "{media_owner}:{media_group}"'
        res = _run_safe(
            conn, test_cmd, cwd=remote_dir, run_as=run_as, hide=True, desc="media owner check"
        )
        if res.exited:
            logger.warning(
                f"⚠️ media/ owner should be {media_owner}:{media_group} (path={media_path})"
            )

    django_env = ""
    if settings_module:
        django_env = f"DJANGO_SETTINGS_MODULE={_q(settings_module)} "

    def run_in_venv(cmd, *, desc=None):
        full = f"bash -lc {_q(f'source {venv_activate} && {cmd}')}"
        return _run_safe(
            conn,
            full,
            cwd=remote_dir,
            run_as=run_as,
            desc=desc,
            hide=False,
        )

    if requirements:
        logger.info("📦 pip install requirements…")
        run_in_venv(f"pip3 install -r {_q(requirements)}", desc="pip install")

    logger.info("🗄️ migrate…")
    run_in_venv(f"{django_env}python {_q(manage_py)} migrate", desc="migrate")

    if collectstatic:
        logger.info("🧱 collectstatic…")
        run_in_venv(
            f"{django_env}python {_q(manage_py)} collectstatic --noinput",
            desc="collectstatic",
        )

    if compilemessages:
        logger.info("🌍 compilemessages…")
        run_in_venv(
            f"{django_env}python {_q(manage_py)} compilemessages",
            desc="compilemessages",
        )

    rtype = (restart_cfg.get("type") or "touch").lower()

    if rtype == "systemd":
        services = restart_cfg.get("services") or []
        for svc in services:
            logger.info(f"🔁 systemd restart {svc}…")
            _run_safe(
                conn,
                f"systemctl restart {_q(svc)}",
                run_as="root",
                desc=f"restart {svc}",
            )

    elif rtype == "touch":
        for p in touch_paths:
            logger.info(f"🫳 touch {p}…")
            _run_safe(
                conn,
                f"touch {_q(p)}",
                cwd=remote_dir,
                run_as=run_as,
                desc=f"touch {p}",
            )

    elif rtype == "none":
        logger.info("⏭️ restart skipped (restart.type=none)")

    else:
        raise ValueError(f"Unknown deploy.restart.type={rtype!r}")

    logger.info("✅ Bare deploy done")
