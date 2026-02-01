# gw-fabric-tools

Reusable Fabric tasks for Ghostwing deployments.

## Requirements

- Python 3.11+ (recommended)
- `pipx` installed and `~/.local/bin` in your `PATH` (`pipx ensurepath`)

## Install (pipx)

`gw-fabric-tools` is meant to be injected into the `fabric` pipx environment.

```bash
pipx install fabric
pipx inject fabric gw-fabric-tools
```

Check installation:

```bash
pipx list
fab --version
```

## Upgrade

```bash
pipx upgrade fabric
pipx inject --force fabric gw-fabric-tools
```

## Uninstall

Remove only this package from the `fabric` pipx environment:

```bash
pipx uninject fabric gw-fabric-tools
```

Remove Fabric entirely:

```bash
pipx uninstall fabric
```

> Note: if `fab` becomes unavailable after uninstall/uninject, run `pipx reinstall fabric`
> and refresh your shell command cache (`rehash` in zsh).

## Development install (editable)

Inject the local repository in editable mode:

```bash
pipx install fabric
pipx inject fabric -e ~/repos/gw-fabric-tools
```

To update after pulling changes:

```bash
cd ~/repos/gw-fabric-tools
git pull
pipx inject --force fabric -e .
```

To remove the editable injection:

```bash
pipx uninject fabric gw-fabric-tools
```

## Usage

Create a `fabfile.py` in your project and import the tasks you want:

```python
try:
    from gw_fabric_tools.data import (  # noqa: F401
        docker_dev_import_data,
        download_data,
        load_data,
        upload_data,
    )
    from gw_fabric_tools.deploy import deploy  # noqa: F401
except ImportError as exc:
    raise SystemExit(
        "\n❌ gw-fabric-tools is not installed.\n"
        "Go to https://codeberg.org/ghostwing/gw-fabric-tools for more information.\n"
    ) from exc
```

List available tasks:

```bash
fab -l
```

Run a task:

```bash
fab deploy --help
fab deploy prod
```

### Renaming tasks

If you need to expose a task under a different name in your project,
you can wrap an existing task and call its underlying body.

```python
from fabric import task
from gw_fabric_tools.deploy import deploy as _deploy_task


@task
def deploy(c):
    print("hello world!")


@task
def gw_deploy(c, env, build_without_cache=False):
    return _deploy_task.body(
        c=c,
        env=env,
        build_without_cache=build_without_cache,
    )
```

This allows you to:
- keep the original task implementation
- expose a project-specific task name
- avoid duplicating logic

## Configuration

Below is an example configuration file used by `gw-fabric-tools`.
It typically lives outside of Git (e.g. `.fab-vars.json`) and defines
how each environment should be deployed.
Don't forget to add the file path in `.gitignore`.

### Example `.fab-vars.json`

```json
{
  "docker-example": {
    "host": "my-host",
    "host_user": "my-user",
    "host_port": 22,
    "remote_type": "docker",
    "run_as": "deploy",
    "web_image_name": "my_docker_image_name",
    "remote_dir": "/path/to/app/files/",
    "copy_data": {
      "include_db": true,
      "include_media": false,
      "create_admin_user_in_docker_dev": true,
      "docker_media_path": "/assets/media/"
    },
    "deploy": {
      "migrate": true
    }
  },
  "bare-example": {
    "host": "my-host",
    "host_user": "my-user",
    "host_port": 22,
    "remote_type": "bare",
    "run_as": "deploy",
    "remote_dir": "/path/to/app/files/",
    "copy_data": {
      "include_db": true,
      "include_media": true,
      "create_admin_user_in_docker_dev": true,
      "media_path": "/var/www/myapp/media/"
    },
    "db": {
      "name": "mydb",
      "user": "mydbuser",
      "password": "mypass",
      "host": "127.0.0.1",
      "port": 5432
    },
    "deploy": {
      "venv_activate": "/var/www/myapp/venv/bin/activate",
      "requirements": "requirements/base.txt",
      "collectstatic": true,
      "compilemessages": true,
      "touch_paths": ["common/wsgi.py"],
      "media_user": "www-data",
      "media_group": "www-data",
      "media_path": "media/"
    }
  }
}
```

### Notes

- Each top-level key represents an environment (e.g. `prod`, `staging`, `docker-dev`)
- `remote_type` can be `docker` or `bare`
- `run_as` defines the Unix user used for privileged operations
- Database settings are only required for `remote_type = "bare"`
- This file is **not committed to Git** (added in `.gitignore`)
