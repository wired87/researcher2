# researcher2

Deep research agent: finds paper URLs (and fetches their content) via **Gemini deep research** or **ChatGPT + LangChain** (default). No Vertex AI RAG.

## Backend

- **`chatgpt`** (default): LangChain + OpenAI + DuckDuckGo search. Set `OPENAI_API_KEY`. Optional: `langchain-openai`, `langchain-community`, `duckduckgo-search`.
- **`gemini`**: Google Gemini deep-research interaction. Set `GEMINI_API_KEY`.

Env: `DEEP_RESEARCH_BACKEND=chatgpt` or `DEEP_RESEARCH_BACKEND=gemini`.

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
