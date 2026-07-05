# PR #155 — deferred review notes

Notes for review comments on [PR #155](https://github.com/Pipelex/pipelex-cookbook/pull/155) that were verified as valid but deferred rather than fixed in the PR.

## `hello-1` plugin route is only defined on the gateway profile

- **Reporter:** Codex (`chatgpt-codex-connector`), P2
- **Location:** `.pipelex/inference/routing_profiles.toml:30` (thread `PRRT_kwDOOwmu9c6OZ6Se`)
- **Origin:** authored in commit `ecb231c` ("Make using_inference_plugins a real entry-point plugin example"), which this PR happens to carry (the branch was cut from a local `dev` that was one unpushed commit ahead). It is not part of this PR's 0.37-migration / validation-gate / methods-cleanup work.

### The issue (confirmed valid)

`optional_routes = { "hello-1" = "hello" }` is declared only on the `all_pipelex_gateway` profile, which is the shipped `active` profile. The `using_inference_plugins` demo (`hello_plugin.mthds`) requests `model = "hello-1"`, and the plugin's README advertises it as running with "no API key and no network". That promise only holds under the default gateway profile: if a user switches `active` to another profile (e.g. `all_openai`, `all_anthropic`), nothing routes `hello-1` to the `hello` backend, so it resolves to that profile's `default` backend and the demo fails even with the plugin installed.

### Why deferred (needs-judgment)

The fix is a design decision on example code, with several valid shapes and no obviously-correct one — the reviewer itself offered two:

1. **Add `optional_routes = { "hello-1" = "hello" }` to every profile.** Makes the demo robust across profiles but clutters a user-facing config template with a demo-only route repeated ~18 times.
2. **A profile-independent / global optional route.** Cleanest conceptually, but may require a pipelex routing-config feature that doesn't exist yet — needs checking upstream.
3. **Document the assumption.** Leave the route on the gateway profile and state in the example README that the zero-key demo assumes the default `all_pipelex_gateway` profile. Lowest effort; narrows the "runs anywhere" claim.

### Recommendation

Lean toward (3) as a quick, honest fix (add a one-line profile note to `examples/c_advanced/using_inference_plugins/README.md`), and open a separate question upstream about whether (2) — a profile-independent optional route — is supported or worth adding. Revisit alongside the `using_inference_plugins` example owner, since this is that example's concern rather than this PR's. Thread left open for follow-up.
