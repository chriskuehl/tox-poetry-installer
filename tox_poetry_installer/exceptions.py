"""Custom plugin exceptions

All exceptions should inherit from the common base exception :exc:`ToxPoetryInstallerException`.

::

  ToxPoetryInstallerException
   +-- LockedDepVersionConflictError
   +-- LockedDepNotFoundError
   +-- ExtraNotFoundError

"""


class ToxPoetryInstallerException(Exception):
    """Error while installing locked dependencies to the test environment"""


class LockedDepVersionConflictError(ToxPoetryInstallerException):
    """Locked dependencies cannot specify an alternate version for installation"""


class LockedDepNotFoundError(ToxPoetryInstallerException):
    """Locked dependency was not found in the lockfile"""


class ExtraNotFoundError(ToxPoetryInstallerException):
    """Project package extra not defined in project's pyproject.toml"""