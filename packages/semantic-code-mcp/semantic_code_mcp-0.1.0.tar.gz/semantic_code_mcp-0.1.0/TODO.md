# TODO

## In Progress

### Search Quality & Output Improvements
Improve search result quality and output format for better usability.

**Tier 1 - Quick Wins:**
- [x] Score threshold filtering - filter out low-confidence results (score < 0.3)
- [x] Remove unused Searcher class - dead code in search/searcher.py
- [x] Truncate long results - cap at ~50 lines with "..." indicator
- [x] Group results by file - sort results so same-file chunks are together
- [ ] Configurable min_score parameter - let callers control the quality threshold (default 0.3)
- [x] Stronger exact match boost - exact phrase/keyword matches should get +30-50% boost, not just +5%
- [x] Hybrid search with keyword fallback - run semantic + keyword search in parallel, merge results. Ensures exact identifier matches surface even with low semantic similarity

**Tier 2 - Medium Effort:**
- [x] Keyword boost (hybrid search) - boost results containing query words literally
- [x] Parallel chunking - use asyncio.gather for parallel file processing
- [x] File recency boost - factor mtime into ranking

**Tier 3 - Larger Effort:**
- [x] Module-level code - extend chunker to capture module docstrings (see decision 003)
- [ ] Background re-indexing - return stale results while re-indexing
- [ ] Separate docstrings - index docstrings separately for better matching
- [ ] Code-specific embedding model - evaluate UniXcoder/CodeBERT

## Pending

### Publish to PyPI for `uvx` Distribution
Currently the server can only run from a local clone (`uv run python -m semantic_code_mcp`). Publishing to PyPI would let users install and run with a single `uvx semantic-code-mcp` command — no clone needed.

**Context:**
- Package already has a build system (hatchling), entry point (`[project.scripts]` → `semantic_code_mcp:main`), and `__init__.py` exports `main`.
- `torch` depends on a custom index (`https://download.pytorch.org/whl/cpu`) for CPU-only builds on Linux. This is configured in `[tool.uv.sources]` which is project-local — it does NOT travel with the published package.
- On macOS and Windows, PyPI `torch` is already CPU-only. The custom index is only needed on Linux to avoid pulling the ~2GB CUDA build.
- GitHub repo: `git@github.com:vrppaul/semantic-code-mcp.git`

**Steps:**

1. **Create PyPI account and API token**
   - Register at https://pypi.org if not already done
   - Create an API token scoped to the `semantic-code-mcp` project (or all projects for the first upload)
   - Store token for use with `uv publish`

2. **Verify package builds cleanly**
   - Run `uv build` and confirm it produces a `.whl` and `.tar.gz` in `dist/`
   - Test the wheel installs correctly: `uvx --from ./dist/semantic_code_mcp-0.1.0-py3-none-any.whl semantic-code-mcp`
   - Verify the entry point runs (`semantic-code-mcp` should start the MCP server on stdin/stdout)

3. **Test `uvx` install with CPU-only torch on Linux**
   - Test: `uvx --index pytorch-cpu=https://download.pytorch.org/whl/cpu --from ./dist/semantic_code_mcp-0.1.0-py3-none-any.whl semantic-code-mcp`
   - Confirm torch CPU-only is installed (not the CUDA build)
   - Test on macOS/Windows without `--index` — should get CPU torch from PyPI automatically

4. **Publish to PyPI**
   - `uv publish` (uses the API token from step 1)
   - Verify install: `uvx semantic-code-mcp` (macOS/Windows) and `uvx --index pytorch-cpu=https://download.pytorch.org/whl/cpu semantic-code-mcp` (Linux)

5. **Update README.md installation section**
   - Keep the existing `uvx semantic-code-mcp` command (already in README)
   - Add Linux-specific note about CPU-only torch with `--index` flag
   - Update Claude Code integration snippet to include `--index` for Linux:
     ```bash
     # macOS / Windows
     claude mcp add --scope user semantic-code -- uvx semantic-code-mcp
     # Linux (CPU-only torch, saves ~1.8GB)
     claude mcp add --scope user semantic-code -- uvx --index pytorch-cpu=https://download.pytorch.org/whl/cpu semantic-code-mcp
     ```
   - Add JSON config example for Claude Desktop / other MCP clients:
     ```json
     {
       "mcpServers": {
         "semantic-code": {
           "command": "uvx",
           "args": ["--index", "pytorch-cpu=https://download.pytorch.org/whl/cpu", "semantic-code-mcp"]
         }
       }
     }
     ```

6. **Set up GitHub Actions for automated publishing (optional)**
   - Publish on GitHub release tag (`v*`)
   - Use PyPI trusted publishers (OIDC, no token needed)

### Multi-language Support
Currently Python only. Need JS/TS for web projects, Rust/Go for systems work. Tree-sitter supports all of these. See decision 004 for architecture analysis.

**Architecture (decided):** Hybrid base class + dispatcher pattern (Option C+D from analysis).
- `BaseTreeSitterChunker` — shared logic (parsing, line extraction, Chunk construction)
- Language-specific subclasses (`PythonChunker`, `GoChunker`, etc.) — AST walking rules only
- `MultiLanguageChunker` — dispatcher by file extension, single `ChunkerProtocol` interface

**Implementation steps:**
- [ ] Refactor `PythonChunker` into `BaseTreeSitterChunker` + `PythonChunker` subclass
- [ ] Add `MultiLanguageChunker` dispatcher
- [ ] Update `Indexer.scan_files()` to accept supported extensions (currently hardcodes `*.py`)
- [ ] Wire `MultiLanguageChunker` in container
- [ ] Add JavaScript/TypeScript chunker (`tree-sitter-javascript`, `tree-sitter-typescript`)
- [ ] Add Go chunker (`tree-sitter-go`) — receiver methods, package comments
- [ ] Add Rust chunker (`tree-sitter-rust`) — impl blocks, `//!` doc comments

### Performance Optimization
Profiling infrastructure added (pyinstrument). Use `SEMANTIC_CODE_MCP_PROFILE=1` to generate profiles.

**Completed:**
- [x] FTS index skip - avoid rebuilding if already exists (~80ms saved per search)
- [x] Batch embedding generation (already implemented)

**Remaining:**
- [ ] LanceDB index tuning (IVF partitions, PQ compression)

## Done

### Reduce Install Size (CPU-only PyTorch)
Configured uv to pull torch from CPU-only PyTorch index. Venv reduced from 7.8GB to 1.7GB (78% smaller). No CUDA/nvidia/triton packages installed.

### Code Quality & Architecture Cleanup
Post-DI cleanup pass. Improved consistency, type safety, and modularity.
- Specific exception types in chunker.py (`OSError`, `ValueError`, `UnicodeDecodeError`) and lancedb.py (`OSError`, `ValueError`, `RuntimeError`)
- `search_hybrid()` split into 30-line method + extracted `_merge_results()`
- Tree-sitter `Node` type hints already present on all chunker methods
- `ty` in pre-commit, all diagnostics fixed

### Services Layer & Strict Linting
Extracted `IndexService` and `SearchService`, architecture review fixes, strict lint config.
- `IndexService` orchestrates scan → detect → chunk → embed with progress + timing
- `SearchService` auto-indexes via `IndexService`, non-optional `SearchOutcome.index_result`
- `server.py` reduced to thin tool layer delegating to services
- SQL injection fix, atomic cache writes, FTS log levels
- Lazy `sentence-transformers` import (torch no longer loaded at startup, ~4s saved)
- Strict ruff rules (C901, DTZ, ASYNC, SLF, PIE, T20, PERF, FURB, PLC0415)
- ty type-checker added to pre-commit with targeted rules

### Dependency Injection Refactor
Converted from direct instantiation to proper DI with a composition root.
- Container with lazy model loading and per-project connection caching
- Global settings singleton (`configure_settings()` / `get_settings()`)
- `app.py` composition root (`create_app()`) wiring settings, logging, profiling, container
- `server.py` stripped to pure tool definitions — no init code
- Shared store/embedder between SearchService and Indexer (no redundant instances)
- `cache_dir` injected into Indexer (no internal `get_index_path` calls)
- Split `models.py` into domain models + `responses.py` for API types
- Real timing data in `SearchOutcome` instead of hardcoded zeros
- `_ensure_table()` made public, dead ranking code removed
- SearchService tests added (10 tests)
