# Bundled JavaScript client

Generated from the pinned release of `@wsrpc/client` published by
[wsrpc-ts](https://github.com/wsrpc/wsrpc-ts). The client is distributed under
the MIT license in `LICENSE`.

The PEP 517 build backend checks every bundled asset against `_build/client.json`.
Missing or changed assets are fetched from the pinned npm archive, verified with
SHA-512, and checked against the asset SHA-256 hashes before being copied here.
Both wheel and sdist include the complete snapshot. Building an unchanged checkout
or an sdist needs neither network access to npm nor Node.js.

To update the pinned client, run from the repository root:

```sh
python -m _build.client 4.5.1
uv build
```

Replace the version with the desired published release. Commit `_build/client.json`
and all changed static assets together. Do not edit the generated client here.
Existing `STATIC_DIR` URLs are preserved, including `wsrpc.min.js` and
`wsrpc.es6.js`; source maps, legacy TypeScript declarations, and the MIT license
come from the same npm archive.
