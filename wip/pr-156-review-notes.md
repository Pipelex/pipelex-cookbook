# PR #156 — deferred review notes

Notes for review comments on [PR #156](https://github.com/Pipelex/pipelex-cookbook/pull/156) that were verified as valid but deferred rather than fixed in the PR.

## `hello-1` plugin route is only defined on the gateway profile (re-raised)

- **Reporter:** Codex (`chatgpt-codex-connector`), P2
- **Location:** `.pipelex/inference/routing_profiles.toml:32` (thread `PRRT_kwDOOwmu9c6Oa0QT`)
- **Status:** Re-raised on this PR. Same comment was already verified-valid and deferred on [PR #155](https://github.com/Pipelex/pipelex-cookbook/pull/155) — the full analysis and the three candidate fixes live in [`pr-155-review-notes.md`](./pr-155-review-notes.md). Not duplicated here.

### Why deferred again (needs-judgment)

Unchanged from PR #155: the demo works out of the box under the shipped `active = "all_pipelex_gateway"` profile (with the `hello` backend enabled and no key). The failure only appears if a user switches `active` to another profile, and the fix is a design decision on example code with several valid shapes and no obviously-correct one. This is the `using_inference_plugins` example owner's call, not this release PR's concern. Thread left open for follow-up.

The other Codex comment on this PR (`tests/e2e/test_bundles.py` — plugin bundle exposed to the live inference run) **was fixed** in this pass (`make install` now editable-installs the plugin + a plugin-presence skip guard), so it is not listed here.
