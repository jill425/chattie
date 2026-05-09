# Chattie Python Migration SDD

> Status: IMPL
> Target directory: `chattie_py/`
> Source system: current TypeScript project in `src/`
> Goal: port Chattie to Python while preserving current behavior and tests at the module boundary.

## 1. Scope

Migrate the existing Chattie service from TypeScript to Python under `chattie_py/`.

The Python version must provide:

- `POST /grade` equivalent API behavior.
- `POST /callback` LINE webhook behavior with signature validation.
- NLP grammar check using LanguageTool.
- NLP scoring and route decision.
- Optional LLM enhancement using Anthropic Messages API.
- LINE reply formatting and reply sending.
- Unit-testable modules matching current TypeScript boundaries.

The TypeScript implementation remains untouched during migration.

## 2. Non-Goals

- Do not delete or rewrite the existing TypeScript project.
- Do not require a database.
- Do not change user-facing grading semantics unless a spec explicitly says so.
- Do not introduce Python framework coupling into core grading logic.

## 3. Directory Layout

```text
chattie_py/
  pyproject.toml
  README.md
  chattie_py/
    __init__.py
    server.py
    api/grading_api.py
    config/env.py
    config/constants.py
    grading/formatter.py
    grading/pipeline.py
    grading/router.py
    grading/types.py
    line/message_filter.py
    line/message_handler.py
    line/reply_helper.py
    line/signature_guard.py
    line/webhook.py
    llm/client.py
    llm/parser.py
    llm/prompt.py
    nlp/client.py
    nlp/scorer.py
    utils/errors.py
    utils/logger.py
    utils/text.py
  tests/
```

## 4. Execution Order

### Phase 1: Scaffold

Status: DONE

- Create Python package directory.
- Add `pyproject.toml`.
- Add Python package modules matching TypeScript module boundaries.
- Add local README with setup and run commands.

### Phase 2: Core Data And Utilities

Status: DONE

- Define dataclasses / typed dictionaries for grading and NLP results.
- Port errors, constants, env parsing, logging, and Chinese text detection.
- Keep all core modules importable without requiring LINE or Anthropic SDKs.

### Phase 3: Pure Core Logic

Status: DONE

- Port message filtering.
- Port NLP scoring.
- Port grading router.
- Port LLM prompt builder.
- Port LLM response parser.
- Port reply formatter.

### Phase 4: External Clients

Status: DONE

- Implement LanguageTool client with stdlib `urllib`.
- Implement Anthropic Messages client with stdlib `urllib`.
- Implement LINE reply helper with stdlib `urllib`.
- External credentials are read from environment at call time.

### Phase 5: HTTP Entry Points

Status: DONE

- Implement stdlib HTTP server.
- `GET /health` returns `OK`.
- `POST /grade` validates JSON body and returns grading result.
- `POST /callback` validates LINE signature, responds immediately, then handles events.

### Phase 6: Tests

Status: DONE

- Add unit tests for pure logic and API validation.
- Tests run with stdlib `unittest`.
- No network is required for tests.

### Phase 7: Verification

Status: DONE

- Run Python unit tests.
- Run Python bytecode compile check.
- Record any remaining gaps.

## 5. Behavioral Requirements

### Text Validation

- Missing or non-string `text` returns `400 invalid_text`.
- Empty trimmed text returns `400 invalid_text`.
- Text longer than 1000 chars returns `400 invalid_text`.
- Text containing Han characters returns `400 invalid_text`.

### Message Filtering

- Non-message events are skipped.
- Non-text messages are skipped.
- Empty text, text over 1000 chars, Han text, URL-heavy text, and low-signal noise are skipped.
- Group and room messages must start with `/check`, `/grade`, or `/fix`.
- Direct user text is graded without a command prefix.

### NLP Scoring

- Ignore LanguageTool `style` matches.
- `misspelling` matches become spelling issues.
- All other non-style matches become grammar issues.
- Grammar score: `max(0, 100 - grammar_issue_count * 20)`.
- Spelling score: `max(0, 100 - spelling_issue_count * 15)`.
- Overall score: rounded average of grammar and spelling scores.

### Routing

- Fewer than 4 words routes to `nlp-only`.
- No NLP issues and at least 4 words routes to `nlp+llm` for fluency checking.
- Invalid score routes to `nlp+llm`.
- Score greater than or equal to threshold routes to `nlp-only`.
- Score below threshold routes to `nlp+llm`.

### LLM

- Prompt must request Australian English.
- LLM parser accepts pure JSON or a JSON object embedded in extra text.
- Missing `suggestion` or `tips` becomes an empty string.
- LLM failures downgrade the grading pipeline to `nlp-only`.

### Reply Formatting

- Include original text.
- Include grammar and spelling blocks when issues exist.
- Show at most 5 issues per block.
- Include LLM suggestion and tips only for `nlp+llm` results.

## 6. Verification Commands

From repository root:

```bash
python3 -m unittest discover tests
python3 -X pycache_prefix=/private/tmp/chattie_pycache -m compileall chattie_py
```

## 7. Completion Criteria

The migration is considered complete for this SDD when:

- `chattie_py/` contains a runnable Python implementation.
- Unit tests pass without network access.
- Python modules compile.
- The root TypeScript project is not modified except for adding migration files.
