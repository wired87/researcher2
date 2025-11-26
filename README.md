# researcher2

## Usage

To run the researcher agent, use the following command:

```bash
python -m researcher2.cli --prompt "Your research prompt here"
```

Or, if you have set the `RESEARCH_PROMPT` environment variable:

```bash
python -m researcher2
```

## Options

- `--prompt`: The research prompt. Overrides the `RESEARCH_PROMPT` environment variable.
- `--output`: The output directory. Overrides the `OUTPUTS` environment variable.
