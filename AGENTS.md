# Kitchen Substitute public content instructions

Read README.md and .github/workflows/publish.yml before publishing changes.
This public repository distributes signed content packs and hosts the
website in docs/. The private app repository owns authoring and generation.

Before credential, remote-host, CI or setup work on Norm's Mac, read
~/Projects/PROJECT_ACCESS_POLICY.md. A checkout grants no credentials or
remote access. Keep private records, credentials, private keys and
authentication caches out of this public repository.

Preserve the validated-copy, signed-release workflow. Run the existing
python3 tools/validate.py for content changes. Preserve pack-version,
manifest, hash and signature compatibility with the app.

content-v* tags trigger signing and GitHub Release publication.
Do not move or duplicate the existing CONTENT_SIGNING_KEY authority.
Do not tag, release or deploy as a verification step.

Preserve website URLs and use the private app repository's existing
generator where applicable. Keep support and privacy information
consistent with the app.
