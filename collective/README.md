# Proton-AI Collective

This directory is the curated, public knowledge feed shared by Proton installations.

## Data flow

1. An installation creates a proposal in its local `collective-outbox/` folder.
2. The owner reviews it and explicitly publishes it using a GitHub token with **Contents: write** permission.
3. The proposal appears under `collective/incoming/`; it is not trusted or used for training.
4. Independent reviewers can assess it. Two approvals are a review threshold, not proof of truth; a maintainer must still curate and approve it.
5. Only records explicitly marked `status: approved` and `training_eligible: true` in `approved.jsonl` are distributed as lessons or exported to the neural training corpus.
6. Every installation can download the public approved feed with `proton-collective sync`.

## Important limitations

- The current local privacy/source/duplicate checks are deterministic checks, **not independent AI agents** and not fact-checking.
- The repository does not yet have external AI reviewer providers configured. Do not describe placeholder checks as other AIs.
- Reviewer identities must be authenticated by a future provider integration. The prototype review-record function is not an authentication system.
- Ownership entries are declarations only. They are never proof of legal trademark or intellectual-property ownership and are excluded from neural training.
- Contributions are proposals, not trusted instructions. Never execute submitted code or shell commands.
- The neural trainer currently learns next-character patterns from a text corpus. Adding approved text changes training data but does not guarantee factual recall, reasoning or coding ability.
- Neural weights are trained centrally in GitHub Actions and distributed as a checkpoint artifact; the artifact is not automatically installed on phones yet.
- Do not upload private conversations, names, addresses, phone numbers, credentials, API keys or other personal information.

## Commands

Create a lesson proposal:

```sh
proton-collective submit "A sourced explanation..." --source https://example.org/article
```

Create an unverified authorship declaration (not used for training):

```sh
proton-collective submit "I declare that I created..." --kind ownership_claim --subject "Example Brand"
```

Publish a specific pending proposal after reviewing it:

```sh
export PROTON_GITHUB_TOKEN="YOUR_TOKEN"
proton-collective publish PROPOSAL_UUID
unset PROTON_GITHUB_TOKEN
```

The token must be a fine-grained GitHub token limited to this repository with Contents: write. Do not paste it into chat or commit it to the repository.

Download approved knowledge:

```sh
proton-collective sync
```

Export only curated lessons for a later neural training run:

```sh
proton-collective export-training
```
