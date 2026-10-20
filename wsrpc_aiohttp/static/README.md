# Bundled JavaScript client

Generated directly from [wsrpc-ts](https://github.com/wsrpc/wsrpc-ts).
The client is distributed under the MIT license in `LICENSE`.
`client-source.json` records the exact Git commit and package-lock checksum
used to produce these assets.

Building a wheel or sdist from the Python repository fetches the current upstream
Git `HEAD`, runs `npm ci --ignore-scripts` and `node tools/build-client.mjs`, then
bundles the resulting ESM, UMD, minified JavaScript, source maps, legacy TypeScript
declarations, and license. This requires Git, Node.js >=22, npm, and network access.
It does not wait for an npm release of `@wsrpc/client`.

The sdist contains the finished client and a frozen build manifest. Building a
wheel from that sdist needs neither Git, Node.js nor access to GitHub/npm. A
corrupted snapshot fails validation instead of silently selecting another client.
Editable installs reuse a valid local snapshot.

To reproduce a specific client revision when building from the Python repository:

```sh
WSRPC_CLIENT_REF=7af746dd053d0a082f83afe51f74d198c486b69a uv build
```

A Git tag or branch is also accepted. Without `WSRPC_CLIENT_REF`, a new source
build fetches current upstream `HEAD` even when the local snapshot is valid.
To refresh the snapshot alone, run `python -m _build.client [GIT_REF]`.
Do not edit generated JavaScript here. Existing `STATIC_DIR` URLs are preserved.
