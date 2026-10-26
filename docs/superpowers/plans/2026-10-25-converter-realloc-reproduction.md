# Native converter reproduction and proposed source fix

1. Reproduce the synthetic UI save failure outside the UI and verify the failed publication preserves the target and backup.
2. Inspect the pinned upstream source and request independent review.
3. Supply a minimal source patch and an anonymous standalone native reproduction; test its generated SQLite/GVAS structure and no-overwrite/hash guards.
4. Check the recorded compiler availability. Do not replace the pinned converter archive without rebuilding, reproducing the binary and passing native regression gates.
5. Keep the evidence and promotion requirements in a dedicated Draft PR. No release, merge or binary substitution.

The runtime failure is consistent with the source use-after-free; the allocator move was not instrumented. The exact compiler from the provenance record is unavailable on this host. The source patch is proposed, not a validated replacement binary.
