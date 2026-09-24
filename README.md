# kitchen-substitute-content — public content distribution

Publishes the signed content packs for the **Kitchen Substitute** iOS app. The private
app repo (`normzeng/kitchen-substitute`) holds the code and docs; THIS repo is the public
distribution point (GitHub Releases serve the files without auth).

Flow: authoring happens in the private repo → the validated `content/kitchen_subs.json`
is copied here → tag `content-v{N}` → Actions validates, signs (ed25519), and publishes
`manifest.json` + `pack.json.gz` as a Release. Installed apps poll the manifest and apply
packs atomically (docs/ARCHITECTURE.md in the private repo).
