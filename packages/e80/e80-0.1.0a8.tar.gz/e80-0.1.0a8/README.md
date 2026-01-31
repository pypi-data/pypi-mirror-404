# 8080 CLI

> [!NOTE]
> If you're just trying to use the 8080 API, see here. (TODO)

Use the 8080 CLI to build, deploy, and run hosted code on the 8080 platform.

Requirements:
  - [uv](https://astral.sh/uv)
  - Python 3.13
  - Docker version 29.1.5, build 0e6fee6 (or later)

## Quickstart

1. Create an 8080 account on https://app.8080.io

1. Install the tool: `uv tool install e80` (installs the `8080` command)

1. Login to your account `8080 login`

1. Initialize a project `8080 init hello-world; cd hello-world`

1. Run your project using the dev server: `8080 dev`

1. Deploy your project to 8080: `8080 deploy`

## More info

See the [e80_sdk](https://pypi.org/project/e80_sdk) package to interface with the 8080 API.
