# Claude Dev CLI

[![PyPI version](https://badge.fury.io/py/claude-dev-cli.svg)](https://badge.fury.io/py/claude-dev-cli)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-303%20passing-brightgreen.svg)](https://github.com/thinmanj/claude-dev-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Homebrew](https://img.shields.io/badge/homebrew-available-orange.svg)](https://github.com/thinmanj/homebrew-tap)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A powerful command-line tool for developers using Claude AI with multi-API routing, test generation, code review, and comprehensive usage tracking.

## Features

### 🌐 Multi-Provider AI Support (v0.14.0+)
- **Anthropic (Claude)**: GPT-4 class models with 200k context
  - Haiku, Sonnet, Opus - full model family
  - Industry-leading context window
- **OpenAI (GPT)**: ChatGPT and GPT-4 models (v0.15.0+)
  - GPT-3.5 Turbo, GPT-4, GPT-4 Turbo
  - Azure OpenAI support
  - Install: `pip install 'claude-dev-cli[openai]'`
- **Ollama (Local)**: Zero-cost local inference (v0.16.0+)
  - Mistral, Mixtral, Code Llama, DeepSeek Coder
  - 100% free, private, offline
  - Install: `pip install 'claude-dev-cli[ollama]'`
- **Provider Abstraction**: Unified interface across all providers
- **Cost Tracking**: Per-provider usage and cost monitoring
- **Graceful Fallback**: Works with any combination of providers

### 🔑 Multi-API Key Management
- **Secure Storage**: API keys stored in system keyring (macOS Keychain, Linux Secret Service, Windows Credential Locker)
- Route tasks to different API keys/providers (personal, client, enterprise, local)
- Automatic API selection based on project configuration
- Automatic migration from plaintext to secure storage

### 🎯 Model Profiles (v0.10.0+)
- **Named Profiles**: Use friendly names instead of full model IDs (`fast`, `smart`, `powerful`)
- **Custom Pricing**: Define input/output costs per Mtok for accurate usage tracking
- **API-Specific Profiles**: Different models and pricing per API config
- **Project Defaults**: Set per-project model preferences
- **Dynamic Resolution**: Profile names automatically resolve to model IDs
- **Built-in Profiles**:
  - `fast`: Claude 3.5 Haiku ($0.80/$4.00 per Mtok)
  - `smart`: Claude Sonnet 4 ($3.00/$15.00 per Mtok) - default
  - `powerful`: Claude Opus 4 ($15.00/$75.00 per Mtok)

### 🚀 Code Generation (v0.12.0+)
- **Generate Code from Specs**: Create new code from descriptions, files, PDFs, or URLs
  - `cdc generate code --description "REST API client" -o client.py`
  - Multiple input sources: text, files (.md, .txt), PDFs, URLs
  - Auto-detects target language from file extension
  - Interactive refinement mode
- **Add Features to Projects**: Analyze existing code and generate implementation plans
  - `cdc generate feature --description "Add authentication" src/`
  - Multi-file analysis and modification
  - Preview mode to review changes before applying
  - Supports same input sources as code generation
- **Multiple Input Sources**:
  - `--description TEXT`: Inline specification
  - `-f/--file PATH`: Read from file
  - `--pdf PATH`: Extract from PDF
  - `--url URL`: Fetch from URL
- **Optional Dependencies**: Install with `pip install 'claude-dev-cli[generation]'`
  - Enables PDF and URL support
  - Graceful fallback if not installed

### 📁 Multi-File Support (v0.11.0+)
- **Batch Processing**: Review, refactor, test, or document multiple files at once
- **Directory Support**: Process all code files in a directory with `--max-files` limit
- **Auto-Detection**: Commands auto-detect git changes when no files specified
  - `cdc review` → reviews staged files, falls back to modified files, then current directory
- **Git Integration**: New `cdc git review` command for reviewing changes
  - `--staged`: Review only staged changes
  - `--branch <range>`: Review branch changes (e.g., `main..HEAD`)
- **Multi-Language**: Supports 25+ file extensions (Python, JS/TS, Go, Rust, Java, C++, etc.)
- **Smart Display**: Shows file list preview (first 5-10 files, then "... and N more")
- Commands with multi-file support:
  - `review`, `refactor`, `generate tests`, `generate docs`

### 🧪 Developer Tools
- **Test Generation**: Automatic pytest test generation for Python code
- **Code Review**: Comprehensive code reviews with security, performance, and best practice checks
- **Debug Assistant**: Analyze errors and get fixes with explanations
- **Documentation**: Generate docstrings and README documentation
- **Refactoring**: Get suggestions for code improvements
- **Git Integration**: Generate conventional commit messages from diffs

### 📊 Usage Tracking
- Track token usage per API key
- Cost estimation based on current pricing
- Filter by date range and API config
- Detailed breakdowns by model, date, and API

### 💬 Interaction Modes
- **Single-shot**: Quick questions with piping support
- **Interactive**: Chat mode with conversation history
- **Streaming**: Real-time responses

### 📝 Custom Templates
- **Built-in Templates**: 8 pre-built templates for common tasks (code review, testing, debugging, etc.)
- **User Templates**: Create and manage your own reusable prompt templates
- **Variable Substitution**: Use {{variable}} placeholders for dynamic content
- **Categories**: Organize templates by category (review, testing, debugging, etc.)

### 🧠 Context Intelligence (v0.8.0+)
- **Auto-Context**: `--auto-context` flag on 7 commands for intelligent context gathering
  - `ask`, `review`, `debug`, `refactor` (v0.8.0)
  - `git commit`, `generate tests`, `generate docs` (v0.8.1)
- **Git Integration**: Automatically include branch, commits, modified files
- **Dependency Analysis**: Parse imports and include related files
- **Multi-Language Error Parsing** (v0.8.2): Python, JavaScript/TypeScript, Go, Rust, Java
- **Context Summary** (v0.8.2): Preview context before API calls with `cdc context summary`
- **Smart Truncation**: Prevent token limits with configurable file size limits
- **Project Memory**: Remember preferences per project
- **Global Config**: Set context defaults in `~/.claude-dev-cli/config.json`

### 🔄 Workflows (v0.7.0+, Enhanced v0.16.1)
- **Multi-Step Automation**: Chain AI operations and shell commands with YAML
- **AI Decision Making**: Use `ask` command to make intelligent workflow decisions (v0.16.1)
- **Variable Interpolation**: Pass data between steps with `{{variable}}` syntax
- **Conditional Execution**: Skip steps based on conditions with `if` clauses
- **Approval Gates**: Human-in-the-loop with `approval_required: true`
- **Model Selection**: Use different AI models per step for cost optimization (v0.16.1)
- **Error Handling**: Continue on failure with `continue_on_error: true`
- **Three Step Types**: command (cdc), shell (bash/zsh), set (variables)
- **Cost Optimization**: Mix free local AI with paid cloud AI strategically

### 🎒 TOON Format Support (Optional)
- **Token Reduction**: 30-60% fewer tokens than JSON
- **Cost Savings**: Reduce API costs significantly
- **Format Conversion**: JSON ↔ TOON with CLI tools
- **Auto-fallback**: Works without TOON installed

## Installation

### Via Homebrew (macOS/Linux)

```bash
# Add the tap
brew tap thinmanj/tap

# Install
brew install claude-dev-cli

# Or in one command
brew install thinmanj/tap/claude-dev-cli
```

### Via pip

#### Basic Installation

Core dependencies only (includes unidiff for diff parsing):

```bash
pip install claude-dev-cli
```

Core dependencies:
- `anthropic>=0.18.0` - Claude API client
- `click>=8.1.0` - CLI framework
- `rich>=13.0.0` - Terminal formatting
- `pydantic>=2.0.0` - Data validation
- `keyring>=24.0.0` - Secure credential storage
- `cryptography>=41.0.0` - Encryption for secure storage
- `pyyaml>=6.0.0` - YAML configuration support
- `unidiff>=0.7.0` - Production-grade diff parsing

#### With Optional Features

**Multi-Provider Support**:

```bash
# OpenAI (GPT) support
pip install 'claude-dev-cli[openai]'

# Ollama (local/free) support
pip install 'claude-dev-cli[ollama]'

# All providers
pip install 'claude-dev-cli[all-providers]'
```

**Code Generation Support** (PDF & URL input):

```bash
pip install 'claude-dev-cli[generation]'
```

Adds:
- `pypdf>=3.0.0` - PDF text extraction
- `requests>=2.28.0` - HTTP client for URL fetching
- `beautifulsoup4>=4.0.0` - HTML parsing

**TOON Format Support** (30-60% token reduction):

```bash
pip install 'claude-dev-cli[toon]'
```

Adds:
- `toon-format>=0.1.0` - TOON encoding/decoding

**Syntax Highlighting** (enhanced diff display):

```bash
pip install 'claude-dev-cli[plugins]'
```

Adds:
- `pygments>=2.0.0` - Syntax highlighting for diffs

**All Optional Features**:

```bash
pip install 'claude-dev-cli[generation,toon,plugins]'
```

**Development Installation** (for contributors):

```bash
pip install 'claude-dev-cli[dev]'
```

Includes all optional features plus:
- `pytest>=7.0.0` - Testing framework
- `black>=23.0.0` - Code formatting
- `ruff>=0.1.0` - Linting
- `mypy>=1.0.0` - Type checking

### Via pipx (Recommended for CLI tools)

pipx provides isolated installations without affecting your system Python:

```bash
# Basic installation
pipx install claude-dev-cli

# With code generation support (PDF & URL)
pipx install 'claude-dev-cli[generation]'

# With TOON support (token reduction)
pipx install 'claude-dev-cli[toon]'

# With syntax highlighting
pipx install 'claude-dev-cli[plugins]'

# With all optional features
pipx install 'claude-dev-cli[generation,toon,plugins]'
```

### Upgrade Existing Installation

```bash
# Upgrade via pip
pip install --upgrade claude-dev-cli

# Upgrade via pipx
pipx upgrade claude-dev-cli

# Upgrade via Homebrew
brew upgrade claude-dev-cli
```

## Quick Start

### 1. Set Up API Keys

```bash
# Add your personal API key
export PERSONAL_ANTHROPIC_API_KEY="sk-ant-..."
cdc config add personal --default --description "My personal API key"
# 🔐 Stored securely in system keyring

# Add client's API key
export CLIENT_ANTHROPIC_API_KEY="sk-ant-..."
cdc config add client --description "Client's Enterprise API"

# List configured APIs (shows storage method)
cdc config list

# Manually migrate existing keys (automatic on first run)
cdc config migrate-keys
```

### 1.1 Setup Ollama (Local/Free Alternative) - v0.16.0+

Run AI models locally with **zero cost** and full privacy using Ollama:

```bash
# Install Ollama (one-time setup)
# macOS/Linux: Download from https://ollama.ai
# Or via Homebrew: brew install ollama

# Start Ollama server
ollama serve  # Run in background or separate terminal

# Install Ollama support
pip install 'claude-dev-cli[ollama]'

# Configure local provider (no API key needed!)
cdc config add ollama local --default
# ℹ️  No API key needed for local provider

# Pull models (one-time per model)
cdc ollama pull mistral      # Fast, general-purpose (7B)
cdc ollama pull codellama    # Code-specialized (7B-34B)
cdc ollama pull mixtral      # Powerful reasoning (8x7B)

# List available models
cdc ollama list
# ┌──────────────┬─────────────────┬─────────┬──────────┬─────────────────┐
# │ Model        │ Display Name    │ Context │ Cost     │ Capabilities    │
# │ mistral      │ Mistral 7B      │ 8,192   │ FREE     │ chat, code      │
# │ codellama    │ Code Llama      │ 16,384  │ FREE     │ code, chat      │
# │ mixtral      │ Mixtral 8x7B    │ 32,768  │ FREE     │ chat, analysis  │
# └──────────────┴─────────────────┴─────────┴──────────┴─────────────────┘

# Show model details
cdc ollama show mistral
```

**Benefits of Local Models:**
- ✅ **Zero Cost**: No API fees, unlimited usage
- ✅ **Privacy**: Data never leaves your machine
- ✅ **Offline**: Works without internet connection
- ✅ **Fast**: No API latency (after model loads)
- ✅ **Control**: Full control over models and data

**Considerations:**
- ⚠️ Requires decent hardware (8GB+ RAM, GPU recommended)
- ⚠️ Models need disk space (4-40GB per model)
- ⚠️ Quality may be lower than GPT-4/Claude Opus
- ⚠️ Initial model download can take time

**Use Local Models:**
```bash
# Use with any command - completely FREE!
cdc ask "explain async/await"
cdc ask -m fast-local "quick question"
cdc generate tests -m code-local mymodule.py
cdc review -m smart-local src/

# Use specific model directly
cdc ask -m mistral "your question"
cdc ask -m codellama "write a function to parse JSON"

# Remote Ollama server
cdc config add ollama remote --base-url http://server:11434
cdc ask -a remote "question"
```

**Available Model Profiles:**
- `fast-local`: mistral (8k context, fast inference)
- `smart-local`: mixtral (32k context, powerful)
- `code-local`: codellama (16k context, code-focused)

### 2. Basic Usage

```bash
# Ask a question (uses 'smart' profile by default)
cdc ask "explain asyncio in Python"

# Use a specific model profile
cdc ask -m fast "quick question"  # Uses Haiku (fast & cheap)
cdc ask -m powerful "complex task"  # Uses Opus 4 (most capable)

# With file context
cdc ask -f mycode.py "review this code"

# Pipe input
cat error.log | cdc ask "what's causing this error?"

# Interactive mode
cdc interactive

# Use specific API
cdc ask -a client "generate tests for this function"
```

### 3. Model Profile Management (v0.10.0+)

```bash
# List available model profiles
cdc model list
# ┌───────────┬──────────────────────────┬────────┬────────┐
# │ Profile   │ Model ID                 │ Input  │ Output │
# │ fast      │ claude-3-5-haiku-...     │ $0.80  │ $4.00  │
# │ smart     │ claude-sonnet-4-...      │ $3.00  │ $15.00 │ ← default
# │ powerful  │ claude-opus-4-...        │ $15.00 │ $75.00 │
# └───────────┴──────────────────────────┴────────┴────────┘

# Add a custom profile
cdc model add lightning claude-3-5-haiku-20241022 \
  --input-price 0.80 --output-price 4.00 \
  --description "Ultra-fast model for simple tasks"

# Set default model profile
cdc model set-default fast  # Use Haiku by default

# Set default for specific API config
cdc model set-default powerful --api enterprise  # Opus for enterprise API

# Show profile details
cdc model show smart

# Remove a profile
cdc model remove lightning

# Use profiles in any command
cdc ask -m fast "simple question"
cdc review -m powerful complex_file.py  # More thorough review
cdc generate tests -m smart mymodule.py  # Balanced approach
```

### 3. Code Generation Commands (NEW in v0.12.0, enhanced v0.13.0)

```bash
# Generate code from specification (single file)
cdc generate code --description "REST API client for weather data" -o client.py
cdc generate code --file spec.md -o implementation.go
cdc generate code --pdf requirements.pdf -o app.js
cdc generate code --url https://example.com/api-spec -o service.py

# Generate multi-file projects (NEW in v0.13.0)
cdc generate code --description "FastAPI REST API with auth" -o my-api/
cdc generate code --file spec.md -o project/ --dry-run  # Preview first
cdc generate code --file spec.md -o project/ --yes  # No confirmation
# Creates complete directory structure with multiple files

# Generate code with interactive refinement
cdc generate code --description "Database ORM" -o orm.py --interactive

# Generate code with project context
cdc generate code --file spec.md -o service.py --auto-context

# Add features to existing project (NEW: multi-file output in v0.13.0)
cdc generate feature --description "Add user authentication with JWT" src/
cdc generate feature --file feature-spec.md
cdc generate feature --pdf product-requirements.pdf --preview
cdc generate feature --url https://example.com/feature-spec

# Preview feature changes before applying
cdc generate feature --description "Add caching layer" src/ --preview
cdc generate feature --description "Add REST API" --dry-run  # Preview changes
cdc generate feature --file spec.md --yes  # Apply without confirmation

# Interactive feature implementation
cdc generate feature --description "Add logging" src/ --interactive

# Hunk-by-hunk approval (like git add -p) - NEW in v0.13.1
cdc generate feature -f spec.md
# At confirmation prompt, type 'patch' to review changes hunk-by-hunk
# Options: y (yes), n (no), s (skip file), q (quit), help
```

### 3.1 Interactive Diff Approval (v0.13.1+)

When applying file modifications, you can review and approve changes hunk-by-hunk, similar to `git add -p`:

```bash
# After generating feature/refactor changes:
cdc generate feature -f spec.md

# At the confirmation prompt:
Continue? (Y/n/preview/patch/help) patch

# For each file:
File: src/main.py
Modify file (3 hunk(s))

Hunk 1/3:
[Shows diff with syntax highlighting]
@@ -10,3 +10,5 @@
 def main():
-    print("old")
+    print("new")
+    logging.info("Started")

Apply this hunk? (y/n/s=skip file/q=quit/help) y  # Approve this hunk

Hunk 2/3:
[Shows next diff]
Apply this hunk? (y/n/s=skip file/q=quit/help) n  # Skip this hunk

Hunk 3/3:
[Shows final diff]
Apply this hunk? (y/n/s=skip file/q=quit/help) s  # Skip remaining in file

# File operations options:
Create this file? (y/n/s=skip/q=quit) y  # For new files
Delete this file? (y/n/s=skip/q=quit) n  # For file deletions
```

**Options:**
- `y, yes` - Apply this hunk/file
- `n, no` - Skip this hunk (keeps original)
- `s, skip` - Skip remaining hunks in current file
- `q, quit` - Stop reviewing and apply approved changes so far
- `edit` - Open files in $EDITOR before applying
- `save` - Save to custom location
- `help` - Show help message

**Benefits:**
- Fine-grained control over changes
- Keep original code for some hunks while applying others
- Syntax-highlighted diffs for easy review
- Edit files before applying for manual tweaks
- Save to custom location without -o flag
- Safe: only approved hunks are written

### 3.2 Edit and Save Options (v0.13.2+)

Before applying changes, you can edit files or save to custom locations:

#### Edit in $EDITOR
```bash
cdc generate feature -f spec.md

# At confirmation:
Continue? (Y/n/preview/patch/edit/save/help) edit

# Opens each file in your $EDITOR (vi, nano, code, etc.)
# Make manual adjustments, save and close
# Changes are applied after editing
```

#### Save to Custom Location
```bash
cdc generate code -d "REST API" -o /tmp/output

# At confirmation:
Continue? (Y/n/preview/patch/edit/save/help) save

# Single file:
Filename: my-custom-name.py  # Save to custom filename

# Multiple files:
Directory: /path/to/output/  # Save entire project elsewhere
```

**Use Cases:**
- **Edit**: Make manual tweaks before applying (fix formatting, adjust logic)
- **Save**: Try changes elsewhere before applying to project
- **Edit + Preview**: Review, edit, then apply with confidence
- **Save for later**: Generate code, save it, review offline, apply manually

**Environment Variables:**
- `$EDITOR`: Your preferred editor (e.g., `export EDITOR=nano`)
- Defaults to `vi` if `$EDITOR` not set

### 4. Developer Commands

```bash
# Generate tests (single file)
cdc generate tests mymodule.py -o tests/test_mymodule.py

# Generate tests for multiple files (NEW in v0.11.0)
cdc generate tests file1.py file2.py file3.py
cdc generate tests src/ --max-files 10

# Generate tests with interactive refinement
cdc generate tests mymodule.py --interactive

# Generate tests with context (includes dependencies, related files) - NEW in v0.8.1
cdc generate tests mymodule.py --auto-context

# Code review (single file)
cdc review mymodule.py

# Code review multiple files (NEW in v0.11.0)
cdc review file1.py file2.py file3.py
cdc review src/  # Review entire directory
cdc review  # Auto-detect git changes (staged → modified → current dir)

# Code review with auto-context (includes git, dependencies, tests)
cdc review mymodule.py --auto-context

# Code review with interactive follow-up questions
cdc review mymodule.py --interactive

# Review git changes (NEW in v0.11.0)
cdc git review --staged  # Review only staged changes
cdc git review --branch main..HEAD  # Review branch changes
cdc git review  # Review all modified files

# Debug errors with intelligent error parsing
python script.py 2>&1 | cdc debug --auto-context

# Generate documentation (single file)
cdc generate docs mymodule.py

# Generate docs for multiple files (NEW in v0.11.0)
cdc generate docs file1.py file2.py file3.py
cdc generate docs src/ --max-files 10

# Generate docs with interactive refinement
cdc generate docs mymodule.py --interactive

# Generate docs with context (includes dependencies) - NEW in v0.8.1  
cdc generate docs mymodule.py --auto-context

# Refactor (single file)
cdc refactor legacy_code.py

# Refactor multiple files (NEW in v0.11.0, enhanced v0.13.0)
cdc refactor file1.py file2.py file3.py
cdc refactor src/
cdc refactor  # Auto-detect git changes

# Multi-file refactoring with preview (NEW in v0.13.0)
cdc refactor src/ --dry-run  # Preview changes
cdc refactor src/ --yes  # Apply without confirmation
cdc refactor src/ --preview  # Review before applying

# Refactor with context (includes related files)
cdc refactor legacy_code.py --auto-context

# Refactor with interactive refinement
cdc refactor legacy_code.py --interactive

# Git commit message
git add .
cdc git commit

# Git commit message with context (includes history, branch) - NEW in v0.8.1
git add .
cdc git commit --auto-context
```

### 5. Context-Aware Operations (v0.8.0+)

```bash
# Auto-context includes: git info, dependencies, related files

# Review with full project context
cdc review mymodule.py --auto-context
# ✓ Context gathered (git, dependencies, tests)

# Debug with parsed error details (multi-language support)
python broken.py 2>&1 | cdc debug -f broken.py --auto-context
node app.js 2>&1 | cdc debug --auto-context  # JavaScript/TypeScript
go run main.go 2>&1 | cdc debug --auto-context  # Go
# ✓ Context gathered (error details, git context)
# Supports: Python, JavaScript, TypeScript, Go, Rust, Java

# Preview context before making API calls - NEW in v0.8.2
cdc context summary mymodule.py
# Shows: files, sizes, lines, estimated tokens, truncation warnings

# Ask questions with file context
cdc ask -f mycode.py --auto-context "how can I improve this?"
# ✓ Context gathered

# Refactor with related files
cdc refactor app.py --auto-context
# Automatically includes imported modules and dependencies
```

### 6. Custom Templates

```bash
# List all templates (built-in and user)
cdc template list

# Show template details
cdc template show code-review

# Add a custom template
cdc template add my-review -c "Review this code for {{focus}}: {{code}}" \
  -d "Custom review template" --category review

# Use a template (interactive variable input)
cdc template use debug-error

# Delete a user template
cdc template delete my-review

# Filter by category
cdc template list --category review

# Show only user templates
cdc template list --user
```

#### Built-in Templates

- **code-review**: Comprehensive code review with customizable focus
- **code-review-security**: Security-focused code review
- **test-strategy**: Generate testing strategy and test cases
- **debug-error**: Debug error with context
- **optimize-performance**: Performance optimization analysis
- **refactor-clean**: Clean code refactoring
- **explain-code**: Detailed code explanation
- **api-design**: API design assistance

### 6. Conversation History & Summarization (NEW in v0.8.3)

```bash
# List recent conversations
cdc history list

# Search conversations
cdc history list --search "python decorators"

# Export conversation
cdc history export 20240109_143022 -o chat.md

# Summarize to reduce token usage
cdc history summarize --latest
cdc history summarize 20240109_143022 --keep-recent 6

# Delete old conversations
cdc history delete 20240109_143022
```

**Auto-Summarization** in interactive mode:
- Automatically triggers when conversation exceeds 8,000 tokens
- Keeps recent messages (default: 4 pairs), summarizes older ones
- Reduces API costs by ~30-50% in long conversations
- Shows token savings after summarization

### 7. Workflows - AI-Powered Automation (v0.7.0+, Enhanced v0.16.1)

Chain multiple AI operations into automated sequences with YAML workflows.

#### Basic Workflow Usage

```bash
# Run a workflow
cdc workflow run my-workflow.yaml

# Pass variables
cdc workflow run workflow.yaml --var file=main.py --var api=local

# List available workflows
cdc workflow list

# Show workflow details
cdc workflow show workflow.yaml
```

#### Example: Simple Review & Test Workflow

```yaml
name: "Review and Test"
description: "Review code and generate tests"

steps:
  - name: code-review
    command: review
    args:
      file: "{{target_file}}"
      api: "local"  # Use FREE local AI
      model: "smart-local"
    output_var: review_result
  
  - name: generate-tests
    command: generate tests
    args:
      file: "{{target_file}}"
      api: "local"
      model: "code-local"
    output_var: tests
  
  - name: run-tests
    shell: "pytest tests/"
    continue_on_error: true
```

**Run it:**
```bash
cdc workflow run review-test.yaml --var target_file=app.py
```

#### Example: AI Decision Making (NEW in v0.16.1)

Use the `ask` command to make intelligent workflow decisions:

```yaml
name: "Adaptive Code Analysis"
description: "AI analyzes code complexity and adapts workflow"

steps:
  # AI rates complexity
  - name: check-complexity
    command: ask
    args:
      prompt: "Rate this code complexity 1-10, respond with number only: {{code}}"
      api: "local"  # FREE
      model: "fast-local"
    output_var: complexity
  
  # Conditional deep review for complex code
  - name: deep-review
    command: review
    args:
      file: "{{file}}"
      api: "personal"  # Use paid API for complex code
      model: "powerful"
    if: "{{complexity}} > 7"
    approval_required: true  # Ask before using paid API
  
  # Simple refactor for medium complexity
  - name: simple-refactor
    command: refactor
    args:
      file: "{{file}}"
      api: "local"  # FREE
    if: "{{complexity}} >= 5 and {{complexity}} <= 7"
```

**Key Features:**
- ✨ `ask` command for AI queries
- 💰 Mix free local and paid cloud AI
- 🎯 Conditional execution based on AI responses  
- ✋ Approval gates before expensive operations

#### Example: Cost-Optimized Workflow

```yaml
name: "Smart Cost Optimization"
description: "Use local AI first, cloud only when critical"

steps:
  # Quick scan with FREE local AI
  - name: quick-scan
    command: ask
    args:
      prompt: "Quick scan for obvious issues: {{code}}"
      api: "local"  # FREE
      model: "fast-local"
    output_var: issues
  
  # Only use expensive cloud AI if critical issues found
  - name: deep-security-analysis
    command: ask
    args:
      prompt: "Deep security analysis: {{code}}"
      api: "personal"  # PAID
      model: "powerful"  # Claude Opus - expensive
      system: "You are a security expert"
    if: "{{issues}} contains 'critical' or {{issues}} contains 'security'"
    approval_required: true
  
  # Tests with local code-specialized model (FREE)
  - name: generate-tests
    command: generate tests
    args:
      file: "{{file}}"
      api: "local"  # FREE
      model: "code-local"
```

**Cost Savings:**
- Local AI for initial scans: $0
- Cloud AI only when needed: saves 70-90%
- Approval gates prevent accidental costs

#### Workflow Step Types

**1. Command Steps (cdc commands)**
```yaml
- name: review-code
  command: review  # or: generate tests, debug, refactor, etc.
  args:
    file: "{{file}}"
    api: "local"
    model: "smart-local"
  output_var: result
```

**Supported commands:** `review`, `generate tests`, `generate docs`, `refactor`, `debug`, `git commit`, `ask` (v0.16.1)

**2. Shell Steps (any command)**
```yaml
- name: run-tests
  shell: "pytest tests/ -v"
  output_var: test_output
  continue_on_error: true
```

**3. Set Steps (variables)**
```yaml
- name: set-config
  set: api_endpoint
  value: "https://api.example.com"
```

#### Advanced Features

**Conditional Execution:**
```yaml
if: "{{score}} > 7"  # Simple comparison
if: "{{result}} contains 'error'"  # String matching
if: "{{tests.success}}"  # Access step results
```

**Approval Gates:**
```yaml
approval_required: true  # Pause for user confirmation
```

**Error Handling:**
```yaml
continue_on_error: true  # Don't stop workflow on failure
```

**Variable Interpolation:**
```yaml
{{variable}}  # Simple variable
{{step_name.output}}  # Step output
{{step_name.success}}  # Step success status
```

#### Example Workflows Included

**Location:** `examples/workflows/`

1. **review-and-refactor.yaml** - Basic review workflow
2. **ai-decision-workflow.yaml** - AI-powered decisions (v0.16.1)
3. **multi-model-workflow.yaml** - Cost optimization (v0.16.1)

### 8. Usage Tracking

```bash
# View all usage
cdc usage

# Last 7 days
cdc usage --days 7

# Filter by API
cdc usage --api client
```

### 9. TOON Format (Optional - Reduces Tokens by 30-60%)

```bash
# Check if TOON is installed
cdc toon info

# Convert JSON to TOON
echo '{"users": [{"id": 1, "name": "Alice"}]}' | cdc toon encode
# Output:
# users[1]{id,name}:
# 1,Alice

# Convert file
cdc toon encode data.json -o data.toon

# Convert TOON back to JSON
cdc toon decode data.toon -o data.json

# Use in workflows
cat large_data.json | cdc toon encode | cdc ask "analyze this data"
```

## Configuration

### Secure API Key Storage

**🔐 Your API keys are stored securely and never in plain text.**

- **macOS**: Keychain
- **Linux**: Secret Service API (GNOME Keyring, KWallet)
- **Windows**: Windows Credential Locker
- **Fallback**: Encrypted file (if keyring unavailable)

Keys are automatically migrated from plaintext on first run. You can also manually migrate:

```bash
cdc config migrate-keys
```

### Global Configuration

Configuration metadata is stored in `~/.claude-dev-cli/config.json` (API keys are NOT in this file):

```json
{
  "api_configs": [
    {
      "name": "personal",
      "api_key": "",  // Empty - actual key in secure storage
      "description": "My personal API key",
      "default": true
    },
    {
      "name": "client",
      "api_key": "",  // Empty - actual key in secure storage
      "description": "Client's Enterprise API",
      "default": false
    }
  ],
  "default_model": "claude-3-5-sonnet-20241022",
  "max_tokens": 4096
}
```

### Project-Specific Configuration

Create `.claude-dev-cli` in your project root:

```json
{
  "name": "My Project",
  "api_config": "client",
  "system_prompt": "You are a Python expert focused on data science.",
  "allowed_commands": ["all"]
}
```

The tool will automatically use the client's API when you run commands in that project!

## API Routing Strategy

### Scenario: Client Work with Enterprise API

```bash
# 1. Set up client's API
export CLIENT_ANTHROPIC_API_KEY="sk-ant-..."
cdc config add client --description "Client Enterprise API"

# 2. Create project config
cd /path/to/client/project
cat > .claude-dev-cli << 'EOF'
{
  "name": "Client Project",
  "api_config": "client",
  "system_prompt": "You are a senior Python developer."
}
EOF

# 3. All commands in this directory now use client's API
cdc generate tests app.py  # Uses client's API
cdc review code.py         # Uses client's API

# 4. Your personal projects use your API
cd ~/my-personal-project
cdc generate tests app.py  # Uses your personal API
```

## What the Client Can See

When using a client's Enterprise API:

✅ **They CAN see:**
- Total API calls and token usage
- Costs associated with the API key
- Potentially conversation history (if enabled by admin)

❌ **They CANNOT see:**
- Which machine you used
- Your other API keys or projects
- Local files unless you sent the content

## Command Reference

### Core Commands

| Command | Description |
|---------|-------------|
| `cdc ask <prompt>` | Ask Claude a question |
| `cdc interactive` | Start interactive chat |
| `cdc usage` | Show usage statistics |

### Configuration

| Command | Description |
|---------|-------------|
| `cdc config add <name>` | Add API configuration |
| `cdc config list` | List all API configs |

### Code Generation

| Command | Description |
|---------|-------------|
| `cdc generate tests <file>` | Generate pytest tests |
| `cdc generate docs <file>` | Generate documentation |

### Code Analysis

| Command | Description |
|---------|-------------|
| `cdc review <file>` | Review code |
| `cdc debug -f <file> -e <error>` | Debug code |
| `cdc refactor <file>` | Refactoring suggestions |

### Templates

| Command | Description |
|---------|-------------|
| `cdc template list` | List all templates |
| `cdc template show <name>` | Show template details |
| `cdc template add <name>` | Add new template |
| `cdc template delete <name>` | Delete user template |
| `cdc template use <name>` | Use template interactively |

### Git Helpers

| Command | Description |
|---------|-------------|
| `cdc git commit` | Generate commit message |

### Workflows (v0.7.0+)

| Command | Description |
|---------|-------------|
| `cdc workflow run <file>` | Execute workflow from YAML |
| `cdc workflow list` | List available workflows |
| `cdc workflow show <file>` | Show workflow details |

### Ollama (Local AI) (v0.16.0+)

| Command | Description |
|---------|-------------|
| `cdc ollama list` | List local models |
| `cdc ollama pull <model>` | Download model |
| `cdc ollama show <model>` | Show model details |

### Model Profiles (v0.10.0+)

| Command | Description |
|---------|-------------|
| `cdc model list` | List all model profiles |
| `cdc model show <name>` | Show profile details |
| `cdc model add <name> <model_id>` | Add custom profile |
| `cdc model set-default <name>` | Set default profile |

## Options

### Common Options

- `-a, --api <name>`: Use specific API config
- `-m, --model <name>`: Use specific Claude model
- `-s, --system <prompt>`: Set system prompt
- `-f, --file <path>`: Include file in prompt
- `-o, --output <path>`: Save output to file

### Model Profiles

**Anthropic (Claude):**
- `fast` / `claude-3-5-haiku-20241022` - Fast & economical ($0.80/$4 per Mtok)
- `smart` / `claude-sonnet-4-5-20250929` - Balanced (default) ($3/$15 per Mtok)
- `powerful` / `claude-opus-4-20250514` - Most capable ($15/$75 per Mtok)

**OpenAI (GPT):** (requires `pip install 'claude-dev-cli[openai]'`)
- `fast-openai` / `gpt-3.5-turbo` - Fast & cheap ($0.50/$1.50 per Mtok)
- `smart-openai` / `gpt-4-turbo` - Balanced ($10/$30 per Mtok)
- `powerful-openai` / `gpt-4` - High capability ($30/$60 per Mtok)

**Ollama (Local - FREE):** (requires `pip install 'claude-dev-cli[ollama]'`)
- `fast-local` / `mistral` - Fast inference (8k context, FREE)
- `smart-local` / `mixtral` - Powerful reasoning (32k context, FREE)
- `code-local` / `codellama` - Code specialist (16k context, FREE)

**Usage:**
```bash
# Use model profile
cdc ask -m fast "quick question"  # Uses Haiku
cdc ask -m fast-local "question"  # Uses Mistral (FREE)

# Use specific model ID
cdc ask -m claude-opus-4-20250514 "complex task"
cdc ask -m gpt-4-turbo "openai task"
```

## Examples

### Test Generation

```bash
# Generate tests for a module
cdc generate tests src/calculator.py -o tests/test_calculator.py

# Review the tests
cdc review tests/test_calculator.py
```

### Code Review Workflow

```bash
# Review before committing
cdc review mycode.py

# Fix issues, then generate commit message
git add mycode.py
cdc git commit
```

### Debugging

```bash
# Run script and analyze errors
python buggy_script.py 2>&1 | cdc debug

# Or debug a specific file
cdc debug -f buggy_script.py -e "NameError: name 'x' is not defined"
```

### Using Multiple APIs

```bash
# Personal work
cdc ask "explain decorators" -a personal

# Client work
cdc generate tests client_code.py -a client

# Check usage per API
cdc usage --api personal
cdc usage --api client
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `{NAME}_ANTHROPIC_API_KEY` | API key for config named "name" |
| `ANTHROPIC_API_KEY` | Default API key |

## Usage Log Format

Usage logs are stored in `~/.claude-dev-cli/usage.jsonl`:

```json
{
  "timestamp": "2024-12-28T03:00:00.000000",
  "api_config": "client",
  "model": "claude-3-5-sonnet-20241022",
  "prompt_preview": "Generate tests for...",
  "input_tokens": 1523,
  "output_tokens": 2847,
  "duration_ms": 3421
}
```

## Development

```bash
# Clone the repository
git clone https://github.com/thinmanj/claude-dev-cli
cd claude-dev-cli

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Julio ([@thinmanj](https://github.com/thinmanj))

## Acknowledgments

- Built with [Anthropic's Claude API](https://www.anthropic.com/)
- CLI powered by [Click](https://click.palletsprojects.com/)
- Beautiful terminal output with [Rich](https://rich.readthedocs.io/)

## Support

- 🐛 [Report bugs](https://github.com/thinmanj/claude-dev-cli/issues)
- 💡 [Request features](https://github.com/thinmanj/claude-dev-cli/issues)
- 📖 [Documentation](https://github.com/thinmanj/claude-dev-cli)
