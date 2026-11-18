# Proton-AI

Proton-AI is an experimental multilingual AI project. This milestone adds a **neural core initialized from random weights** and keeps helper teachers separate from that core.

## Architecture

- **Proton neural core:** a small decoder-only Transformer in PyTorch. Training updates its own weights using a local text corpus.
- **Teacher helpers:** separate programming, science, and general review agents. These first helpers use transparent rules; they are not LLMs and do not guarantee factual correctness.
- **Existing components:** the repository also contains early Rust, C++17, TypeScript, JavaScript, and shell components. They are prototypes and are not yet fully integrated with the neural training engine.

## Install the research engine

Python 3.10+:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On Windows activate with `.venv\\Scripts\\activate`.

## Commands

```bash
proton-train --hours 0.05
proton-train --hours 0.1 --max-steps 100
proton-chat
```

The trainer starts from random weights, uses `data/starter.txt`, and saves `checkpoints/proton-latest.pt`. The included corpus is only a tiny smoke-test corpus. It is not enough to create a knowledgeable assistant. Add lawful, relevant, reviewed training text before expecting useful language ability.

## What “15 hours” means

`--hours 15` is a maximum runtime, not a promise of intelligence or a target quality. A model needs a suitable architecture, large and diverse datasets, validation, and enough compute. Begin with a short run. Do not leave a phone training unattended for 15 hours: mobile devices can overheat or suspend background processes. Use suitable hardware and monitor temperature and resource use.

## Important distinctions

- Saving notes is memory; it does not change neural weights.
- The training loop in `proton/train.py` performs real gradient-based weight updates.
- The teacher helpers review examples separately; they do not secretly replace or train the Proton core.
- This is a tiny research prototype, not a competitive general-purpose chatbot.
- The current checkpoint is saved, but automatic resume, robust validation, dataset provenance tooling, and teacher-model integrations remain future work.

## Safety

External datasets and teacher outputs are untrusted text. Proton must never execute dataset content as code. Keep API keys and passwords out of Git. Use only data you have permission to train on.
