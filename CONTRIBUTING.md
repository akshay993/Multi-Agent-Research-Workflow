# Contributing

## Reporting a Bug

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (`make check` or `docker-compose logs`)

## Requesting a Feature

Open an issue describing what you want and why before building — this avoids duplicate work and ensures the change fits the project direction.

## Contributing Code

1. Fork the repo and create a branch (`git checkout -b feat/your-feature`)
2. Make your changes
3. Ensure the app builds and runs: `make build && make up`
4. Open a PR referencing the related issue

Keep PRs focused — one change per PR. Describe what changed and why, not just what.

## Things to Keep in Mind

- Do not commit `.env` or any secrets
- The known limitations in the README (no cancellation, no retry, no resume) are intentional for the MVP — PRs addressing these are welcome, but open an issue to discuss the approach first
