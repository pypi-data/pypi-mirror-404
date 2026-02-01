from functools import lru_cache
from getpass import getpass

from fabric import Config, Connection


@lru_cache(maxsize=64)
def _get_connection_cached(
    host: str,
    user: str,
    port: int,
    needs_sudo: bool,
) -> Connection:
    kwargs = {"host": host, "user": user, "port": port}

    if needs_sudo:
        sudo_password = getpass("Sudo password (for remote sudo): ")
        kwargs["config"] = Config(
            overrides={"sudo": {"password": sudo_password, "prompt": "auto-sudo-pass"}}
        )

    return Connection(**kwargs)


def get_connection(cfg: dict, *, needs_sudo: bool = False) -> Connection:
    return _get_connection_cached(
        host=cfg["host"],
        user=cfg["host_user"],
        port=int(cfg.get("host_port", 22)),
        needs_sudo=bool(needs_sudo),
    )
