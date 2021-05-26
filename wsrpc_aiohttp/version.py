author_info = (("Dmitry Orlov", "me@mosquito.su"),)

package_info = "WSRPC is the RPC over WebSocket for aiohttp"
package_license = "Apache Software License"

team_email = "me@mosquito.su"

version_info = (3, 2, 0)


__author__ = ", ".join("{} <{}>".format(*info) for info in author_info)
__version__ = ".".join(map(str, version_info))


__all__ = (
    "author_info",
    "package_info",
    "package_license",
    "team_email",
    "version_info",
    "__author__",
    "__version__",
)
