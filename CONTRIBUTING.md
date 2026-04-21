# Contributing

Run the documented CI validation before opening a pull request:

```bash
python3 scripts/quality.py ci
```

Run the broader local validation checks when you change plugin packaging, marketplace wiring, or runtime error handling:

```bash
python3 scripts/quality.py local
```

If you change the skill instructions, helper output, or routing behavior, also run the live authenticated validation steps in [docs/TESTING.md](docs/TESTING.md).
