# Historical NAOqi SDK snapshot

`pynaoqi-python2.7-2.5.7.1-win32-vs2013/` is the original bundled Windows SDK.
The directory name targets Python 2.7, 32-bit Windows and Visual Studio 2013.
It is not a Python 3 dependency and cannot be treated as a cross-platform wheel.

Vendor binaries and wrappers are retained unchanged for historical completeness;
none were executed during cleanup. Obtain a Pepper-compatible SDK and its
installation instructions from the responsible institution/vendor. Use the
matching interpreter/architecture and vendor-documented library paths.

The repository does not reproduce a full robot environment. The top-level
configuration checker and offline tests can run without this SDK. Only explicit
robot startup imports the vendor modules.

See [third-party notes](../THIRD_PARTY.md) for the owner's redistribution
confirmation and the limits of the available license documentation.
