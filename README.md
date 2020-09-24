# tox-poetry-installer

A plugin for [Tox](https://tox.readthedocs.io/en/latest/) that allows test environment
dependencies to be installed using [Poetry](https://python-poetry.org/) using its lockfile.

⚠️ **This project is alpha software and should not be used in a production capacity** ⚠️

![image](https://img.shields.io/pypi/l/tox-poetry-installer)
![image](https://img.shields.io/pypi/v/tox-poetry-installer)
![image](https://img.shields.io/pypi/pyversions/tox-poetry-installer)

**Documentation**

* [Installation and Usage](#installation-and-usage)
* [Limitations](#limitations)
* [Why would I use this?](#what-problems-does-this-solve) (What problems does this solve?)
* [Developing](#developing)
* [Contributing](#contributing)
* [Roadmap](#roadmap)
  * [Path to Beta](#path-to-beta)
  * [Path to Stable](#path-to-stable)

Related resources:
* [Poetry Python Project Manager](https://python-poetry.org/)
* [Tox Automation Project](https://tox.readthedocs.io/en/latest/)
* [Tox plugins](https://tox.readthedocs.io/en/latest/plugins.html)


## Installation and Usage

1. Install the plugin from PyPI:

```
poetry add tox-poetry-installer --dev
```

2. Remove all version specifications from the environment dependencies in `tox.ini`:

```ini
# This...
[testenv]
description = My cool test environment
deps =
    requests >=2.19,<3.0
    toml == 0.10.0
    pytest >=5.4

# ...becomes this:
[testenv]
description = My cool test environment
deps =
    requests
    toml
    pytest
```

3. Run Tox with the `--recreate` flag to rebuild the test environments:

```
poetry run tox --recreate
```

4. 💸 Profit 💸


## Limitations

* In general, any command line or INI settings that affect how Tox installs environment
  dependencies will be disabled by installing this plugin. A non-exhaustive and untested
  list of the INI options that are not expected to work with this plugin is below:
  * [`install_command`](https://tox.readthedocs.io/en/latest/config.html#conf-install_command)
  * [`pip_pre`](https://tox.readthedocs.io/en/latest/config.html#conf-pip_pre)
  * [`downloadcache`](https://tox.readthedocs.io/en/latest/config.html#conf-downloadcache) (deprecated)
  * [`download`](https://tox.readthedocs.io/en/latest/config.html#conf-download)
  * [`indexserver`](https://tox.readthedocs.io/en/latest/config.html#conf-indexserver)
  * [`usedevelop`](https://tox.readthedocs.io/en/latest/config.html#conf-indexserver)
  * [`extras`](https://tox.readthedocs.io/en/latest/config.html#conf-extras)

* When the plugin is enabled all dependencies for all environments will use the Poetry backend
  provided by the plugin; this functionality cannot be disabled on a per-environment basis.

* Alternative versions cannot be specified alongside versions from the lockfile. All
  dependencies are installed from the lockfile and alternative versions cannot be specified
  in the Tox configuration.


## Why would I use this?

**Introduction**

The lockfile is a file generated by a package manager for a project that lists what
dependencies are installed, the versions of those dependencies, and additional metadata that
the package manager can use to recreate the local project environment. This allows developers
to have confidence that a bug they are encountering that may be caused by one of their
dependencies will be reproducible on another device. In addition, installing a project
environment from a lockfile gives confidence that automated systems running tests or performing
builds are using the same environment that a developer is.

[Poetry](https://python-poetry.org/) is a project dependency manager for Python projects, and
as such it creates and manages a lockfile so that its users can benefit from all the features
described above. [Tox](https://tox.readthedocs.io/en/latest/#what-is-tox) is an automation tool
that allows Python developers to run tests suites, perform builds, and automate tasks within
self contained [Python virtual environments](https://docs.python.org/3/tutorial/venv.html).
To make these environments useful, Tox supports installing per-environment dependencies.
However, since these environments are created on the fly and Tox does not maintain a lockfile,
there can be subtle differences between the dependencies a developer is using and the
dependencies Tox uses.

This is where this plugin comes into play.

By default Tox uses [Pip](https://docs.python.org/3/tutorial/venv.html) to install the
PEP-508 compliant dependencies to a test environment. A more robust way to do this is to
install dependencies directly from the lockfile so that the version installed to the Tox
environment always matches the version Poetry specifies. This plugin overwrites the default
Tox dependency installation behavior and replaces it with a Poetry-based installation using
the dependency metadata from the lockfile.

**The Problem**

Environment dependencies for a Tox environment are usually done in PEP-508 format like the
below example

```ini
# tox.ini
...

[testenv]
description = Some very cool tests
deps =
    foo == 1.2.3
    bar >=1.3,<2.0
    baz

...
```

Perhaps these dependencies are also useful during development, so they can be added to the
Poetry environment using this command:

 ```
 poetry add foo==1.2.3 bar>=1.3,<2.0 baz --dev
 ```

 However there are three potential problems that could arise from each of these environment
 dependencies that would _only_ appear in the Tox environment and not in the Poetry
 environment:

 * **The `foo` dependency is pinned to a specific version:** let's imagine a security
   vulnerability is discovered in `foo` and the maintainers release version `1.2.4` to fix
   it. A developer can run `poetry remove foo && poetry add foo^1.2` to get the new version,
   but the Tox environment is left unchanged. The developer environment specified by the
   lockfile is now patched against the vulnerability, but the Tox environment is not.

* **The `bar` dependency specifies a dynamic range:** a dynamic range allows a range of
  versions to be installed, but the lockfile will have an exact version specified so that
  the Poetry environment is reproducible; this allows versions to be updated with
  `poetry update` rather than with the `remove` and `add` used above. If the maintainers of
  `bar` release version `1.6.0` then the Tox environment will install it because it is valid
  for the specified version range, meanwhile the Poetry environment will continue to install
  the version from the lockfile until `poetry update bar` explicitly updates it. The
  development environment is now has a different version of `bar` than the Tox environment.

* **The `baz` dependency is unpinned:** unpinned dependencies are
  [generally a bad idea](https://python-poetry.org/docs/faq/#why-are-unbound-version-constraints-a-bad-idea),
  but here it can cause real problems. Poetry will interpret an unbound dependency using
  [the carrot requirement](https://python-poetry.org/docs/dependency-specification/#caret-requirements)
  but Pip (via Tox) will interpret it as a wildcard. If the latest version of `baz` is `1.0.0`
  then `poetry add baz` will result in a constraint of `baz>=1.0.0,<2.0.0` while the Tox
  environment will have a constraint of `baz==*`. The Tox environment can now install an
  incompatible version of `baz` that cannot be easily caught using `poetry update`.

All of these problems can apply not only to the dependencies specified for a Tox environment,
but also to the dependencies of those dependencies, and so on.

**The Solution**

This plugin requires that all dependencies specified for all Tox environments be unbound
with no version constraint specified at all. This seems counter-intuitive given the problems
outlined above, but what it allows the plugin to do is offload all version management to
Poetry.

On initial inspection, the environment below appears less stable than the one presented above
because it does not specify any versions for its dependencies:

```ini
# tox.ini
...

[testenv]
description = Some very cool tests
deps =
    foo
    bar
    baz

...
```

However with the `tox-poetry-installer` plugin installed this instructs Tox to install these
dependencies using the Poetry lockfile so that the version installed to the Tox environment
exactly matches the version Poetry is managing. When `poetry update` updates the lockfile
with new dependency versions, Tox will automatically install these new versions without needing
any changes to the configuration.

All dependencies are specified in one place (the lockfile) and dependency version management is
handled by a tool dedicated to that task (Poetry).


## Developing

This project requires Poetry-1.0+, see the [installation instructions here](https://python-poetry.org/docs/#installation).

```bash
# Clone the repository...
# ...over HTTPS
git clone https://github.com/enpaul/tox-poetry-installer.git
# ...over SSH
git clone git@github.com:enpaul/tox-poetry-installer.git

# Create a the local project virtual environment and install dependencies
cd tox-poetry-installer
poetry install

# Install pre-commit hooks
poetry run pre-commit install

# Run tests and static analysis
poetry run tox
```


## Contributing

All project contributors and participants are expected to adhere to the
[Contributor Covenant Code of Conduct, Version 2](CODE_OF_CONDUCT.md).

* To report a bug, request a feature, or ask for assistance, please
  [open an issue on the Github repository](https://github.com/enpaul/tox-poetry-installer/issues/new).
* To report a security concern or code of conduct violation, please contact the project author
  directly at **ethan dot paul at enp dot one**.
* To submit an update, please
  [fork the repository](https://docs.github.com/en/enterprise/2.20/user/github/getting-started-with-github/fork-a-repo)
  and
  [open a pull request](https://github.com/enpaul/tox-poetry-installer/compare).


## Roadmap

This project is under active development and is classified as alpha software, not yet ready
usage in production systems.

* Beta classification will be assigned when the initial feature set is finalized
* Stable classification will be assigned when the test suite covers an acceptable number of
  use cases

### Path to Beta

- [ ] Verify that primary package dependencies (from the `.package` env) are installed
      correctly using the Poetry backend.
- [ ] Support the [`extras`](https://tox.readthedocs.io/en/latest/config.html#conf-extras)
      Tox configuration option
- [ ] Add per-environment Tox configuration option to fall back to default installation
      backend.
- [ ] Add detection of a changed lockfile to automatically trigger a rebuild of Tox
      environments when necessary.
- [ ] Add warnings when an unsupported Tox configuration option is detected while using the
      Poetry backend.
- [ ] Add trivial tests to ensure the project metadata is consistent between the pyproject.toml
      and the module constants.
- [ ] Update to use [poetry-core](https://github.com/python-poetry/poetry-core)
      Tox configuration option) and improve robustness of the Tox and Poetry module imports
      to avoid potentially breaking API changes in upstream packages.

### Path to Stable

Everything in Beta plus...

- [ ] Add tests for each feature version of Tox between 2.3 and 3.20
- [ ] Add tests for Python-3.6, 3.7, and 3.8
- [ ] Add Github Actions based CI
- [ ] Add CI for CPython, PyPy, and Conda
- [ ] Add CI for Linux and Windows
