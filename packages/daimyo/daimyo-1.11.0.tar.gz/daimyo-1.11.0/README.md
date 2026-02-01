# Daimyo - Rules Server for Agents

Daimyo (大名) is an extensible Python server providing rules to AI agents through REST and MCP interfaces. Supports scope-based rules with inheritance, categories for filtering, and server federation for distributed rule management.

## Features

- **Multiple Interfaces**: REST API, MCP (Model Context Protocol), and CLI
- **Scope Inheritance**: Single and multiple parent inheritance with priority-based conflict resolution
- **Rule Types**: Commandments (MUST) and Suggestions (SHOULD)
- **Categories**: Organize rules into hierarchical categories for selective retrieval
- **Server Federation**: Distribute scopes across multiple servers with automatic merging
- **Multiple Formats**: Output as YAML, JSON, or Markdown
- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **Templating System**: Rules can use Jinja2 templates to be defined as generic rules that change their form depending on the context
- **Extensibility via Plugins**: Plugins can extend the features of daimyo instances
- **Configurable Markdown Formatting**: Prologues/epilogues, XML tag wrapping, and aggregated display modes

## Installation

```bash
pip install daimyo
```

Or install from source:

```bash
git clone https://gitlab.com/Kencho1/daimyo.git
cd daimyo
pip install -e .
```

## Quick Start

### 1. Set Up Your Rules

```bash
mkdir -p .daimyo
cp -r example-daimyo-rules .daimyo/rules
```

### 2. Start the Server

```bash
daimyo serve
```

### 3. Access the API

Visit http://localhost:8000/docs for interactive API documentation.

```bash
curl http://localhost:8000/api/v1/scopes/python-general/rules
```

## Core Concepts

### Scopes

Scopes represent organizational contexts (company, team, project). Each scope is a directory containing:

- `metadata.yml` - Scope configuration and parent references
- `commandments.yml` - Mandatory rules (MUST)
- `suggestions.yml` - Recommended rules (SHOULD)

```text
.daimyo/rules/
├── python-general/
│   ├── metadata.yml
│   ├── commandments.yml
│   └── suggestions.yml
└── team-backend/
    ├── metadata.yml
    ├── commandments.yml
    └── suggestions.yml
```

### Metadata Format

```yaml
name: scope-name
description: Human-readable description
parents:
  - parent-scope-1
  - parent-scope-2
tags:
  team: backend
  language: python
```

**Fields:**

- `name`: Scope identifier (must match directory name)
- `description`: Human-readable description
- `parents`: List of parent scopes (first = highest priority)
- `tags`: Key-value pairs for organizing scope metadata (e.g., team, language, environment)

### Categories

Categories are hierarchical subdivisions within rules:

```yaml
python.web.testing:
  when: When testing web interfaces
  ruleset:
    - Use playwright for acceptance tests
    - Use pytest fixtures for test setup
```

**Category Tags (Optional):**

Categories can include tags for additional metadata:

```yaml
development.coding.python:
  when: When writing Python code
  tags:
    - python
    - backend
    - performance-critical
  ruleset:
    - Use type hints for all function signatures
    - Follow PEP 8 naming conventions
```

Tags are displayed in markdown output: `<tags>backend; performance-critical; python</tags>`

#### Optional "when" Descriptions

The "when" field is optional. When omitted or empty, the system uses intelligent fallback:

```yaml
python.testing:
  when: When writing tests for this project
  ruleset:
    - Use our custom test fixtures

python.web:
  ruleset:
    - Follow team web standards
```

**Fallback priority**:

1. **Category's merged "when" description**: After scope merging (local extends remote, child extends parent scope), the category's "when" field is used if non-empty
2. **Parent categories in the hierarchy**: If empty, traverse up the category path (e.g., `python.web.testing` → `python.web` → `python`) looking for a non-empty "when"
3. **Default**: "These rules apply at all times"

The scope merging process (local → remote → parent) happens before the hierarchical fallback, ensuring child scopes can override descriptions from remote servers or parent scopes.

This allows:

- Parent/remote scopes to define general descriptions
- Child scopes to override only when needed
- Hierarchical inheritance from broader to specific categories
- Simplified child scopes that inherit descriptions

### Rule Types

**Commandments (MUST)**: Mandatory rules that accumulate through inheritance

**Suggestions (SHOULD)**: Recommended rules that can be overridden or appended with `+` prefix

### Why not nesting the categories?

While it seems more intuitive, it proved to be confusing and harder to maintain in certain cases, e.g.:

- Appending suggestions: it's confusing to know whether the `+` must be prepended to the innermost category, to the root category, or to a category in between.
- Sharding categories: should it combine the innermost category or every category and subcategory defined?

For that reason it was decided to keep the categories at the root level, using the explicit path notation and nesting them logically using the dot path splitting.

## Usage

### REST API

Start the server:

```bash
daimyo serve
daimyo serve --host 0.0.0.0 --port 8080
```

Get rules:

```bash
curl http://localhost:8000/api/v1/scopes/python-general/rules

curl -H "Accept: application/json" \
  http://localhost:8000/api/v1/scopes/python-general/rules

curl -H "Accept: text/markdown" \
  http://localhost:8000/api/v1/scopes/python-general/rules
```

List available scopes:

```bash
curl http://localhost:8000/api/v1/scopes
```

Filter by categories:

```bash
curl "http://localhost:8000/api/v1/scopes/team-backend/rules?categories=python.web,python.testing"
```

Debug mode (skip template expansion):

```bash
# Get raw rules without template rendering
curl "http://localhost:8000/api/v1/scopes/python-general/rules?debug=true"

# Get raw category index without template rendering
curl "http://localhost:8000/api/v1/scopes/python-general/index?debug=true"
```

The `debug` parameter (default: `false`) skips Jinja2 template expansion and returns the original, unprocessed content. This is useful for:

- Viewing the original rules and categories as defined in YAML files
- Debugging why templates may be changing content unexpectedly in production
- Inspecting template syntax before variables are substituted

### MCP Server

Start the MCP server:

```bash
# Using stdio transport (default)
daimyo mcp

# Using HTTP transport
daimyo mcp --transport http

# Using HTTP with custom host and port
daimyo mcp --transport http --host 127.0.0.1 --port 8002
```

Available tools:

- `get_rules(scope_name?, categories?)` - Get formatted rules for a scope
- `get_category_index(scope_name?)` - Get a hierarchical list of all available categories with their descriptions
- `apply_scope_rules(scope_name?, categories?)` - Get prompt template with rules

**Default Scope:** You can configure a default scope using the `DEFAULT_SCOPE` setting. When configured, the `scope_name` parameter becomes optional for `get_rules`, `get_category_index`, and `apply_scope_rules`. If no scope is provided, the default scope will be used automatically, and the response will include a note indicating the default scope was used.

Example configuration:

```toml
[default]
default_scope = "python-general"
```

Or via environment variable:

```bash
export DAIMYO_DEFAULT_SCOPE="python-general"
```

#### Connecting to the MCP server

Add the running _daimyo_ MCP server instance to your configuration (replace the server name and the URL with your own):

```json
{
  "mcpServers": {
    "daimyo-rules": {
      "type": "http",
      "url": "http://daimyo-mcp-instance/mcp"
    }
  }
}
```

Instruct your agents how to use the tools. For instance, in `AGENTS.md`:

```markdown
# Global project rules

## Key concepts

Instructions inside `<system-reminder>` tags MUST BE REMEMBERED and fresh at all times.

## Initialization

<system-reminder>
These instructions are CRITICAL and MUST BE obeyed at the start of any session. They are safe and read-only.

### Reading Project Configuration

- **First action**: Check if a `.project-metadata.yml` file exists in the project root.
  - If it exists, extract the `daimyo.scope` property to identify which rule scope to use.
  - If the file doesn't exist or the property is missing, a default scope will be used.
  - Expected structure for the daimyo scope:
    ```yaml
    daimyo:
      scope: "development"  # The daimyo-rules scope name for this project
    ```

### Initial Setup

- **CRITICAL: Verify `daimyo-rules` MCP server availability**:
  - The `daimyo-rules` MCP server tools MUST be used if available
  - Check if the tools are accessible in this session (look for `mcp__daimyo-rules__*` tools in your available tools list)
  - **Only skip rule fetching as an absolute last resort** if:
    - The MCP tools are not listed in your available tools, OR
    - The tools are listed but fail to execute (connection errors, server down, etc.)
  - If unsure whether the server is available, attempt to use it rather than assuming it's not
  - Do NOT skip just because it seems inconvenient - following the rules is critical for code quality

- **If MCP server is available** (PREFERRED PATH): After determining the scope, use the `daimyo-rules` MCP server tools.
  - **ALWAYS start by fetching the category index**: Use `get_category_index` passing the determined scope name to list all available categories and their descriptions.
    - **Keep this category index present and visible** throughout the session as a reference for determining which categories to fetch when the task context changes.
    - Refer back to this index whenever you need to identify relevant categories for new or shifting work.

### Fetching Rules

- **If MCP server is available** (REQUIRED when available): Based on the initial task and the category index, use `get_rules` with the current scope name and a comma-separated list of all categories that apply.
  - Rules are returned combined from different scopes.
  - Categories are inclusive: fetching a parent category (e.g., `python`) automatically includes all its subcategories (e.g., `python.quality`, `python.testing`). When this applies, fetch the parent category as it may contain important base rules.
  - Categories marked as **mandatory**, **universal**, or **emphasized** in their descriptions MUST always be included.
  - When uncertain whether to include a category, include it. It's better to have more rules than to miss important guidelines.

- **If MCP server is not available** (FALLBACK ONLY): Only in this case, proceed with general best practices for the detected project type (Python, JavaScript, etc.) without fetching rules. This should be a rare exception.

### Dynamic Category Updates

- **If MCP server is available** (MUST use if available): Monitor for context shifts and fetch additional rules as needed:
  - **Monitor for context shifts**: When the focus or nature of the task changes during the session, immediately fetch additional relevant categories:
    - Examples of context shifts:
      - Moving from implementation to testing
      - Switching from coding to documentation
      - Changing programming languages or frameworks
      - Shifting from development to deployment/DevOps tasks
      - Moving from backend to frontend work
    - When a shift occurs:
      1. Consult the category index (kept from initialization)
      2. Identify which new categories are now relevant
      3. Fetch those categories using `get_rules` with the new category list
      4. **Additive approach**: The new rules complement (not replace) previously fetched rules

  - **Proactive category fetching**: If you anticipate needing rules from a new domain based on the conversation direction, fetch them preemptively rather than waiting until they're critically needed.

  - **Re-fetch the category index** if you need a refresher on available categories or if you suspect there might be relevant categories you're not aware of.
</system-reminder>
```

Note some less capable models (like local models via Ollama) may need additional or more detailed instructions.

To make the instructions reusable, the scope name can be read from a file (for instance `.project-metadata.yml`).

### CLI Commands

```bash
# List all available scopes
daimyo list-scopes

# Show details of a specific scope
daimyo show python-general

# View template context for debugging
daimyo context python-general
daimyo context python-general --category python.testing
daimyo context python-general --format json
daimyo context python-general --sources

# Version information
daimyo --version
```

#### Template Context Command

The `context` command displays the Jinja2 template context available when rendering rules for a scope. This is useful for debugging template issues and understanding what variables are available in templates.

**Basic usage:**

```bash
daimyo context <scope_name>
```

**Options:**

- `--category, -c`: Show context for a specific category (includes category key and when description)
- `--format, -f`: Output format - `yaml` (default), `json`, or `table`
- `--sources, -s`: Annotate each variable with its source (config, scope, category, or plugins)

**Examples:**

```bash
# View context in YAML format (default)
daimyo context python-general

# View context for a specific category
daimyo context python-general --category python.testing

# JSON format for programmatic use
daimyo context python-general --format json

# Table format for quick scanning
daimyo context python-general --format table

# Show variable sources
daimyo context python-general --sources
```

**Output includes:**

- **Configuration variables**: All DAIMYO_* settings from environment or config files
- **Scope metadata**: name, description, tags, sources
- **Category info**: key and when description (if --category specified)
- **Plugin context**: Variables provided by enabled plugins
- **Plugin metadata**: Available Jinja2 filters and tests from plugins

## Best Practices for Defining Scopes, Categories, and Rules

**Understanding the Foundation:**

Before diving into best practices, it's crucial to understand how scopes and categories work together:

- **Categories form a universal namespace**: A category like `development.coding.python.testing` has the same meaning across all scopes. Categories are NOT scope-specific.

- **Multiple scopes can contain rules for the same category**: For example, `python-general`, `team-backend`, and `project-api` might all have rules for `development.coding.python.testing`.

- **Scopes are organizational contexts**: They group related categories and rules for specific purposes (company-wide standards, team conventions, project-specific requirements).

- **Scope inheritance merges rules**: When you request rules from a scope with parents, you get merged results for each category across the inheritance chain.

This universal category namespace ensures consistency: when different scopes add rules to `development.security`, they're all contributing to the same logical category.

---

### Part I: Organizational Foundations

#### 1. Understanding Universal vs Conditional Categories

**Universal categories** - Always apply when their domain is relevant:

```text
development.coding.quality → Always applies when writing code
development.coding.python → Always applies when writing Python
general → Always applies
```

**Conditional categories** - Only apply when explicitly chosen or context matches:

```text
development.architecture_patterns.clean_architecture → ONLY when pattern chosen
development.coding.testing → ONLY when writing tests
development.lifecycle.review → ONLY during review phase
```

**Rule:** Clearly separate universal from conditional in your hierarchy. Don't mix them at the same level.

**Anti-pattern:**

```text
development.coding
  ├── architecture (universal - SOLID, DRY)
  └── clean_architecture (conditional - specific pattern)
```

**Better:**

```text
development.coding
  └── architecture (universal - SOLID, DRY)

development.architecture_patterns
  └── clean_architecture (conditional - specific pattern)
```

#### 2. Designing Hierarchical Structures

**Use Aggregator Categories with "Do Not Use Directly" Warnings**

**Purpose:** Provide logical grouping without forcing over-fetching

```text
development.coding [DO NOT USE DIRECTLY; pick relevant subcategories]
  ├── core (universal code rules)
  ├── python (language-specific)
  ├── security (security rules)
  └── testing (conditional - when writing tests)
```

**Benefit:** Users can:

- Fetch `development.coding.python` (specific)
- Skip `development.coding.testing` (conditional)
- Avoid accidentally fetching everything under `development.coding`

#### Hierarchical Inclusion is Automatic

**Remember:** Fetching a parent includes ALL children

**Implication:**

- Place conditional categories as siblings, not children of universal categories
- If a parent has mixed universal/conditional children, users can't selectively exclude

**Example problem:**

```text
development.coding.python (universal for Python)
  ├── implementation (universal)
  ├── quality (universal)
  └── testing (conditional - ONLY when writing tests)
```

Fetching `development.coding.python` forces inclusion of testing rules even when not writing tests.

**Solutions:**

1. Document clearly that testing is conditionally included
2. Move testing to sibling: `development.coding.python_testing`
3. Support exclusion in API: `exclude=["development.coding.python.testing"]`

#### 3. Splitting and Merging Categories

**When to Split**

Split categories when:

1. **Different applicability conditions**

   ```text
   development.coding.python.implementation (always for Python)
   development.coding.python.testing (only when writing tests)
   ```

2. **Different granularity needed**

   ```text
   development.coding.security.design (architectural patterns)
   development.coding.security.implementation (coding practices)
   ```

3. **Rules serve different phases/activities**

   ```text
   development.lifecycle.implementation
   development.lifecycle.review
   development.lifecycle.deployment
   ```

4. **Domain-specific rules exist**

   ```text
   development.domain_specific.web_applications
   development.domain_specific.apis
   development.domain_specific.cli_tools
   ```

**Don't Split When:**

- Rules always apply together - Keep them in one category
- Only 1-2 rules exist - Too granular; merge into parent
- Split creates ambiguity - Which category gets which rule?

**When to Merge**

Merge categories when:

1. **Always fetched together**

   ```text
   # Before: Always fetch both
   development.coding.core
   development.coding.standards

   # After: Merged
   development.coding.core
   ```

2. **Redundant scoping**

   ```text
   # Before: Confusing split
   security (top-level universal)
   development.coding.security.global (also universal?)

   # After: Clarify relationship or merge
   development.security.core (all universal security)
     ├── mindset (high-level principles)
     └── implementation (coding practices)
   ```

3. **Single rule in category**

   ```text
   # Before: Wasteful
   development.architecture_patterns.core
     → Rule: "Prefer well-known patterns"

   # After: Move to parent or merge
   development.architecture_patterns
     → Description includes this guidance
   ```

#### 4. Naming Conventions

**Use Descriptive, Unambiguous Names**

**Avoid:**

- `global` - ambiguous; use `universal` (applies across all scopes) or `core` (base rules for this domain) instead
- `common` - vague
- `misc` - catch-all anti-pattern

**Prefer:**

- `core` - base rules for this category domain
- `universal` - applies across all scopes when this domain is relevant
- `implementation` - during active coding
- `design` - architectural level

**Use "Aggregated" in Descriptions for Parent Categories**

```text
development.coding.python
  Description: "Aggregated rules that apply when the task involves Python programming"
```

Signals that this is a logical grouping with subdivisions.

---

### Part II: Writing Effective Content

#### 5. Writing Clear Descriptions

#### Format: "[Applicability] [What it contains]"

**Universal category:**

```text
development.coding.quality
  Description: "Code quality standards applied during implementation"
```

**Conditional category:**

```text
development.coding.testing
  Description: "Rules for writing and structuring tests. Apply when creating test code"
```

**Conditional pattern (emphasize):**

```text
development.architecture_patterns.clean_architecture
  Description: "Clean architecture rules. **ONLY apply when implementing clean architecture pattern**"
```

#### Use Bold for Critical Conditions

Make conditions unmissable:

- "**ONLY apply when...**"
- "**DO NOT use directly; always pick the relevant subcategories**"
- "**Security must be enforced**"

#### Be Explicit About Timing/Context

**Good:**

- "Apply when writing Python tests"
- "During active code development"
- "When designing system architecture"
- "For all code handling user input"

**Bad:**

- "For testing" (writing tests or running tests?)
- "Python rules" (all Python contexts or specific ones?)
- "Architecture" (designing it or following a pattern?)

**Common Ambiguity Sources**

Avoid these patterns:

1. **"Rules related to X"** - Too vague
   - Better: "Rules for writing X" or "Rules applied when X"

2. **"When appropriate"** - Who decides?
   - Better: "When {specific condition}" or "Unless explicitly excluded"

3. **"General" or "Common"** - General within what scope?
   - Better: "Universal" or "Core" with explicit scope

4. **Passive voice** - "Rules that are applied..."
   - Better: "Apply these rules when..."

**Test Your Descriptions**

Ask: "Can someone reading this description know EXACTLY when to include this category?"

```text
# Ambiguous
development.coding.testing
  Description: "Testing rules"

# Clear
development.coding.testing
  Description: "Rules for writing and structuring tests. Apply when creating test code (test_*.py, *_test.py files)"
```

#### 6. Writing Actionable Rules

**Use MUST/SHOULD Consistently**

**MUST** - Non-negotiable requirements (use commandments):

```text
- MUST: No code comments in generated code
- MUST: Security by default
- MUST: Follow SOLID principles
```

**SHOULD** - Strong recommendations (use suggestions):

```text
- SHOULD: Prefer pytest for testing
- SHOULD: Use ruff for linting
- SHOULD: Use English in code
```

**Make Rules Actionable**

```text
# Bad (not actionable)
- SHOULD: Write good tests
- MUST: Be secure

# Good (actionable)
- SHOULD: Use pytest.mark.parametrize for tests with multiple input scenarios
- MUST: Validate and sanitize all user inputs before processing
```

**One Concern Per Rule**

```text
# Bad (multiple concerns)
- MUST: Use type hints and validate them with mypy, and also use ruff for linting

# Good (separated)
- SHOULD: Use statically-typed code
- SHOULD: Use mypy to validate typing
- SHOULD: Use ruff for linting
```

---

### Part III: Common Organizational Patterns

#### 7. Security Categories

#### Security Deserves Multiple Locations

**Pattern:**

```text
security (top-level category)
  → "Universal security mindset. ALWAYS applies across all scopes"
  → High-level: Security is first-class citizen

development.coding.security
  ├── core: "Universal security requirements for code"
  ├── design: "Security architecture patterns"
  └── implementation: "Secure coding practices"
```

**Why both?**

- Top-level `security` category: Ensures security is NEVER forgotten (always included)
- `development.coding.security` category: Specific implementation requirements

#### Security Should Be

- Mandatory (MUST, not SHOULD)
- Explicit in descriptions ("Critical for web applications, APIs...")
- Subdivided by concern (design vs implementation)
- Referenced in domain-specific categories (web apps mention OWASP, CORS, etc.)

#### 8. Language-Specific Organization

**Pattern: `coding.{language}.{aspect}`**

```text
development.coding.python
  ├── implementation (tooling, structure, conventions)
  ├── quality (linting, type checking)
  └── testing (test framework practices)

development.coding.javascript
  ├── implementation (npm, ESLint, project structure)
  ├── quality (TypeScript, strict mode)
  └── testing (Jest patterns)
```

**Benefits:**

- Consistent across languages
- Easy to add new languages
- Clear aspect separation

**Alternative (if many languages):**

```text
development.coding.languages
  ├── python.*
  ├── javascript.*
  └── rust.*
```

---

### Part IV: Scope-Level Design

#### 9. Designing Scopes

**When to Create Separate Scopes**

Create separate scopes when:

1. **Different teams/projects with distinct rule sets**

   ```text
   backend-team (scope)
   frontend-team (scope)
   ml-team (scope)
   ```

2. **Different enforcement levels**

   ```text
   company-wide (scope) → mandatory for everyone
   team-backend (scope) → specific to backend team
   project-xyz (scope) → overrides for specific project
   ```

3. **Different domains with non-overlapping rules**

   ```text
   development (scope) → coding rules
   operations (scope) → deployment, monitoring
   documentation (scope) → writing docs
   ```

**Scope Composition and Inheritance**

Design scopes to be composable:

```text
Query: get_rules(scopes=["company-wide", "development", "python-web"])

Result: Merged rules from all three scopes
```

This allows:

- Company-wide universal policies
- Development-specific coding standards
- Project-specific overrides

---

### Part V: Quality Assurance

#### 10. Anti-Patterns to Avoid

**Catch-All Categories**

```text
development.coding.misc
development.other
```

Sign of poor organization.

**Deeply Nested Hierarchies (>4 levels)**

```text
development.coding.languages.python.frameworks.django.testing.unit
```

Too granular; hard to navigate.

**Duplicated Rules**

Same rule in multiple categories without clear reason.

**Circular Dependencies**

Category A includes rules about when to use Category B.

**Implementation Details in Descriptions**

```text
Description: "Stored in database table rules_python"
```

Keep descriptions user-focused.

#### 11. Maintenance Guidelines

**Regular Audits**

1. **Check for orphaned rules** - Rules that don't fit their category
2. **Verify applicability** - Do descriptions still match rule content?
3. **Remove dead rules** - Deprecated tools, outdated practices
4. **Consolidate sparse categories** - <3 rules might belong elsewhere

**Versioning Strategy**

Consider versioning for rule changes:

```text
development.coding.python.v2
development.coding.python.v1 (deprecated)
```

Or use scope versioning:

```text
development-2024 (scope)
development-2025 (scope)
```

#### 12. Quick Reference Checklist

When creating scopes/categories/rules, verify:

- [ ] **Applicability is crystal clear** - No guessing when to include
- [ ] **Universal and conditional are separated** - Different hierarchy levels
- [ ] **Names are descriptive and unambiguous** - No "global", "misc", "common"
- [ ] **Descriptions state WHEN to apply** - "Apply when..." or "ONLY when..."
- [ ] **Security is mandatory and explicit** - MUST rules, multiple locations
- [ ] **Hierarchies are logical** - Max 3-4 levels deep
- [ ] **Parent categories have warnings** - "DO NOT USE DIRECTLY" where needed
- [ ] **Rules are actionable** - Specific, measurable, implementable
- [ ] **MUST vs SHOULD is consistent** - Clear distinction
- [ ] **One concern per rule** - No compound requirements
- [ ] **No catch-all categories** - Everything has a proper home
- [ ] **Language-specific rules follow consistent pattern** - Same structure for each language

---

### Part VI: Advanced Techniques

#### 13. Maximizing LLM Effectiveness

The previous sections covered **how to organize rules** (categories, scopes, hierarchies). This section addresses **how to format and present rules to LLMs** for maximum impact and compliance.

**Why Rule Presentation Matters**

- **The Problem**: LLMs process rules as part of larger context windows containing instructions, code, conversations, and other content. Rules can get "lost" or de-prioritized when mixed with this content.
- **The Challenge**: Without explicit semantic markers, LLMs treat rules as just another piece of text, applying similar attention weights to rules and general context.
- **The Solution**: Use semantic markup and structural cues that LLMs are specifically trained to recognize and prioritize.

**A. XML Tag Wrapping: Making Rules Unmissable**

**Recommended Configuration:**

```toml
commandments_xml_tag = "system-reminder"
suggestions_xml_tag = "system-suggestion"
```

**Why This Works:**

1. **Semantic Salience**: LLMs are trained to pay special attention to `<system-*>` tags
   - These tags appear in system prompts during LLM training
   - They signal "important instructions to follow"
   - Higher activation strength compared to plain markdown

2. **Clear Rule Type Distinction**:
   - `<system-reminder>` for MUST rules → Mandatory requirements
   - `<system-suggestion>` for SHOULD rules → Strong recommendations
   - The tag names themselves communicate urgency and flexibility

3. **Better Context Separation**:
   - XML structure creates clear boundaries
   - Prevents rules from blending into surrounding text
   - Easier for attention mechanisms to isolate and process

**Example Transformation:**

*Before (plain markdown):*

```markdown
- **MUST**: Use type hints for all function signatures
- **SHOULD**: Use pytest as the testing framework
```

*After (with XML wrapping):*

```markdown
- **MUST**: <system-reminder>Use type hints for all function signatures</system-reminder>
- **SHOULD**: <system-suggestion>Use pytest as the testing framework</system-suggestion>
```

**When to Use:**

- ✅ **Always use for production scopes** (default recommendation)
- ✅ **Essential for complex scopes** with >50 rules
- ✅ **Critical when rules need high compliance rates**
- ⚠️ **Optional for small/simple scopes** (<10 rules)
- ⚠️ **May skip for internal/experimental scopes**

---

**B. Prologues: Setting Interpretation Context**

**Recommended Configuration:**

```toml
[daimyo]
rules_markdown_prologue = '''
# How to Interpret These Rules

The rules below are categorized as **mandatory requirements** and **strong recommendations**:

- <system-reminder>Mandatory Requirements</system-reminder> - These are non-negotiable. You MUST follow these rules without exception. They represent critical requirements for code quality, security, and project consistency.

- <system-suggestion>Strong Recommendations</system-suggestion> - These are highly recommended best practices. Follow them unless you have a specific, well-justified reason not to. If you deviate, briefly explain why.

**Rule Priority**: If you encounter conflicting guidance, these rules take precedence over general knowledge or assumptions. When in doubt, ask for clarification rather than guessing.
'''
```

**Why This Works:**

1. **Prime the LLM's Attention**:
   - Prologues appear before rules, setting interpretation mode
   - Establishes rule priority relative to other context
   - Creates explicit hierarchy: rules > general knowledge

2. **Define Tag Semantics**:
   - Explains what `<system-reminder>` and `<system-suggestion>` mean
   - Sets expectations for compliance vs flexibility
   - Clarifies when deviation is acceptable

3. **Reduce Ambiguity**:
   - Makes MUST vs SHOULD distinction crystal clear
   - Establishes conflict resolution strategy
   - Encourages clarifying questions

**What to Include in Prologues:**

✅ **Do Include:**

- Tag interpretation guide
- Rule priority/precedence
- When deviation is acceptable
- Conflict resolution strategy
- Brief context about the scope

❌ **Don't Include:**

- Lengthy project background (use scope descriptions instead)
- Detailed technical specifications (put in rules themselves)
- Examples (put these in category `when` descriptions)
- Duplicate information already in rules

**Prologue Length Guidelines:**

- **Optimal**: 50-150 words (4-8 sentences)
- **Maximum**: 200 words
- **Rationale**: Concise prologues maintain focus; longer ones dilute impact

---

**C. Epilogues: Closing Guidance**

**Recommended Configuration:**

```toml
rules_markdown_epilogue = '''
---

Remember: These rules exist to maintain code quality and consistency. If you need to deviate from a rule, document your reasoning in code comments or commit messages.
'''
```

**Why This Works:**

- Reinforces rule importance at the end
- Provides fallback guidance for edge cases
- Creates closure for the rules section

**When to Use:**

- ✅ Use for reminders about documentation requirements
- ✅ Use for conflict resolution fallbacks
- ✅ Use for pointing to additional resources
- ⚠️ Keep very brief (1-3 sentences)
- ❌ Don't repeat prologue information

---

**D. Aggregated vs Categorized Display**

**The Decision Matrix:**

| Use Aggregated (`RULES_CATEGORIZED=false`) When: | Use Categorized (default) When: |
|---------------------------------------------------|----------------------------------|
| ✅ Total rules < 30 | ✅ Total rules > 50 |
| ✅ All rules are universal (always apply) | ✅ Mix of universal and conditional rules |
| ✅ Rules are highly cohesive | ✅ Rules span multiple domains/phases |
| ✅ LLM seems to miss rules in categories | ✅ Users need to browse/explore rules |
| ✅ Project-specific overrides (tight scope) | ✅ General/reusable scopes |

**Why Aggregation Works:**

1. **Reduces Cognitive Load**:
   - Eliminates hierarchical navigation overhead
   - All rules visible in single scan
   - No "hidden" rules in nested categories

2. **Maximizes Attention**:
   - Flat list = equal weight to all rules
   - No category headings to distract
   - Direct, immediate access to requirements

3. **Better for Small, Focused Scopes**:
   - Project-specific rules (tight, cohesive)
   - Framework-specific conventions
   - Team-specific overrides

**Why Categorization Works:**

1. **Scales to Large Rule Sets**:
   - More than 50 rules need organization
   - Categories create logical groupings
   - Easier to maintain and update

2. **Conditional Rule Application**:
   - "Testing" category only needed when writing tests
   - "Security.Design" vs "Security.Implementation"
   - Phase-specific rules (design, implementation, review)

3. **Discoverability**:
   - Users can browse what's available
   - Understand rule scope and applicability
   - Navigate to relevant sections

---

**E. Category Tags: Semantic Metadata**

**Recommended Usage:**

```yaml
development.coding.python.testing:
  when: When writing tests for Python code
  tags: ["testing", "quality-assurance", "pytest", "conditional"]
  ruleset:
    - Use pytest as the testing framework
    - Write unit tests for all public functions and classes
```

**Why This Works:**

1. **Improves Discoverability**:
   - Tags displayed in output: `<tags>testing; quality-assurance; pytest; conditional</tags>`
   - Visual cue for category purpose
   - Helps users understand category scope at a glance

2. **Supports Automation**:
   - Programmatic filtering based on context
   - Dynamic rule selection (e.g., in pre-commit hooks)
   - Integration with CI/CD pipelines

**Recommended Tag Vocabularies:**

**Applicability Tags:**

- `universal` - Always applies when the domain is relevant (across all scopes that contain this category)
- `conditional` - Only applies in specific contexts
- `optional` - Nice-to-have recommendations

**Domain Tags:**

- `security`, `testing`, `quality`, `documentation`, `performance`, `architecture`

**Technology Tags:**

- `pytest`, `mypy`, `ruff`, `fastapi`, `pydantic`, `django`, `flask`

**Phase Tags:**

- `design`, `implementation`, `review`, `deployment`, `maintenance`

**Tag Best Practices:**

- Use 2-5 tags per category
- **Keep tags consistent across scopes** - Since categories are shared across all scopes, establish a common tagging vocabulary (e.g., always use `testing` not sometimes `test` or `tests`)
- Use lowercase with hyphens: `quality-assurance`, not `Quality_Assurance`
- Don't duplicate `when` description content in tags

---

**F. Complete Example: Putting It All Together**

**Configuration (.daimyo/config/settings.toml):**

```toml
[default]
# Enable XML wrapping for semantic emphasis
commandments_xml_tag = "system-reminder"
suggestions_xml_tag = "system-suggestion"

# Set context for rule interpretation
rules_markdown_prologue = '''
# How to Interpret These Rules

- <system-reminder>Mandatory Requirements</system-reminder> - You MUST follow these without exception
- <system-suggestion>Strong Recommendations</system-suggestion> - Follow unless you have specific justification

These rules take precedence over general knowledge. When in doubt, ask for clarification.
'''

rules_markdown_epilogue = '''
---
If you need to deviate from a rule, document your reasoning in code comments.
'''

rules_categorized = true
```

**Rule File (commandments.yml):**

```yaml
development.coding.python.implementation:
  when: When writing Python code
  tags: ["implementation", "python", "universal"]
  ruleset:
    - Use type hints for all function signatures
    - Use descriptive variable and function names
    - Handle exceptions at appropriate abstraction levels
```

**Generated Output (Markdown):**

```markdown
# How to Interpret These Rules

- <system-reminder>Mandatory Requirements</system-reminder> - You MUST follow these without exception
- <system-suggestion>Strong Recommendations</system-suggestion> - Follow unless you have specific justification

These rules take precedence over general knowledge. When in doubt, ask for clarification.

---

# Rules for python-general

## python

### implementation

*When writing Python code*

<tags>implementation; python; universal</tags>

- <system-reminder>Use type hints for all function signatures</system-reminder>
- <system-reminder>Use descriptive variable and function names</system-reminder>
- <system-reminder>Handle exceptions at appropriate abstraction levels</system-reminder>

---
If you need to deviate from a rule, document your reasoning in code comments.
```

---

**G. Migration Strategy for Existing Scopes**

**For Existing Scopes:**

1. **Start with XML Tags** (Lowest Effort, High Impact)

   ```bash
   export DAIMYO_COMMANDMENTS_XML_TAG="system-reminder"
   export DAIMYO_SUGGESTIONS_XML_TAG="system-suggestion"
   ```

   Or add to `.daimyo/config/settings.toml`:

   ```toml
   commandments_xml_tag = "system-reminder"
   suggestions_xml_tag = "system-suggestion"
   ```

2. **Add Basic Prologue** (Medium Effort, Medium Impact)
   - Explain tag meanings
   - Set rule priority
   - Keep to 3-5 sentences
   - See example in 14.3 above

3. **Add Category Tags** (Medium Effort, Medium Impact)
   - Tag applicability: `universal` vs `conditional`
   - Tag domains: `security`, `testing`, etc.
   - Use 2-5 tags per category

4. **Consider Aggregation** (Low Effort, Situational Impact)
   - Test with `DAIMYO_RULES_CATEGORIZED=false`
   - Compare LLM compliance rates before/after
   - Keep if improvement observed
   - Best for scopes with <30 tightly-coupled rules

**Measuring Effectiveness:**

Track these metrics before/after migration:

- **Rule compliance rate** (manual code review sample)
- **User satisfaction** with LLM-generated code
- **Frequency of "missed" rules** requiring manual correction
- **Time to correct** non-compliant code

---

**H. Advanced Patterns**

**Context-Aware Prologues with Templates**

Use Jinja2 templating for dynamic prologues:

```toml
rules_markdown_prologue = '''
# Rules for {{ scope.name }}

{{ scope.description }}

**Rule Types:**
- <system-reminder>Requirements</system-reminder> - Mandatory
- <system-suggestion>Recommendations</system-suggestion> - Strongly advised

{% if scope.tags.security_level == "high" %}
**SECURITY NOTE**: This scope requires elevated security practices.
{% endif %}
'''
```

---

**I. Common Pitfalls to Avoid**

❌ **Over-wrapping**: Don't wrap category names or `when` descriptions in XML tags

```yaml
# WRONG - Only wrap rule text, not category keys or when descriptions
<system-reminder>development.coding.python</system-reminder>:
  when: <system-reminder>When writing Python code</system-reminder>
```

❌ **Verbose Prologues**: Keep prologues under 150 words

```toml
# WRONG - Too long, dilutes attention
rules_markdown_prologue = "This comprehensive scope contains an extensive collection of rules... [500 word essay]"
```

❌ **Mismatched Tags**: Don't use different XML tags than explained in prologue

```toml
# WRONG - Prologue says "system-reminder" but config uses "commandment"
commandments_xml_tag = "commandment"  # Doesn't match prologue explanation!
```

❌ **Aggregating Large Scopes**: Don't use flat display for >50 rules

```toml
# WRONG - 100+ rules in flat list is overwhelming
rules_categorized = false  # When scope has 100+ rules - use categories instead!
```

❌ **Redundant Tag Content**: Don't duplicate `when` description in tags

```yaml
# WRONG - Tag is redundant with when description
development.coding.python.testing:
  when: When writing tests for Python code
  tags: ["when-writing-tests-for-python-code"]  # Just use semantic tags!

# RIGHT - Tags add semantic metadata
development.coding.python.testing:
  when: When writing tests for Python code
  tags: ["testing", "quality-assurance", "pytest", "conditional"]
```

❌ **Inconsistent Tag Vocabulary**: Don't use different tags for same concepts across scopes

```yaml
# WRONG - Inconsistent naming
scope1: tags: ["unit-testing", "quality"]
scope2: tags: ["tests", "qa"]

# RIGHT - Consistent vocabulary
scope1: tags: ["testing", "quality-assurance"]
scope2: tags: ["testing", "quality-assurance"]
```

---

## Configuration

Configuration is managed via `.daimyo/config/settings.toml` or environment variables. Daimyo supports flexible configuration paths for different deployment scenarios.

### Configuration Discovery

Daimyo discovers configuration files and rules directories using a precedence hierarchy that supports local development, user-level defaults, and system-wide deployments.

#### Configuration File Discovery

Configuration files are discovered in the following order (first found wins):

1. **CLI flag**: `--config` / `-c` option
2. **Environment variable**: `DAIMYO_CONFIG_FILE`
3. **Local project**: `.daimyo/config/settings.toml`
4. **User home**: `~/.daimyo/config/settings.toml`
5. **System-wide**: `/etc/daimyo/config/settings.toml`
6. **Default**: `.daimyo/config/settings.toml` (may not exist)

#### Rules Directory Discovery

Rules directories are discovered in the following order (first found wins):

1. **CLI flag**: `--rules-path` / `-r` option
2. **Environment variable**: `DAIMYO_RULES_PATH`
3. **Configuration file**: `RULES_PATH` setting from discovered config
4. **Local project**: `.daimyo/rules` (if exists)
5. **User home**: `~/.daimyo/rules` (if exists)
6. **System-wide**: `/etc/daimyo/rules` (if exists)
7. **Default**: `.daimyo/rules` (may not exist)

#### Deployment Scenarios

**Local Development** (default):
```
project/
├── .daimyo/
│   ├── config/settings.toml
│   └── rules/
```

**User-Level Defaults** (personal defaults across all projects):
```bash
mkdir -p ~/.daimyo/config ~/.daimyo/rules
cp config.toml ~/.daimyo/config/settings.toml
cp -r my-rules/* ~/.daimyo/rules/

# Now works from any directory
cd /tmp/new-project
daimyo list-scopes  # Uses ~/.daimyo/
```

**System-Wide Deployment** (shared across all users):
```bash
sudo mkdir -p /etc/daimyo/config /etc/daimyo/rules
sudo cp config.toml /etc/daimyo/config/settings.toml
sudo cp -r rules/* /etc/daimyo/rules/
```

**Docker/Custom Paths**:
```bash
# Using CLI flags
daimyo --config /app/config.toml --rules-path /app/rules serve

# Using environment variables
export DAIMYO_CONFIG_FILE=/app/config.toml
export DAIMYO_RULES_PATH=/app/rules
daimyo serve
```

### CLI Configuration Override

All CLI commands support global configuration options that must be specified before the command:

```bash
# Override configuration file
daimyo --config /custom/config.toml list-scopes
daimyo -c ~/.daimyo/config/settings.toml serve

# Override rules directory
daimyo --rules-path /custom/rules show my-scope
daimyo -r ~/rules list-scopes

# Override both
daimyo --config /custom/config.toml --rules-path /custom/rules mcp
daimyo -c /custom/config.toml -r /custom/rules serve
```

**Available global options:**

- `--config PATH` / `-c PATH`: Path to configuration file
- `--rules-path PATH` / `-r PATH`: Path to rules directory
- `--version` / `-v`: Show version and exit

**Examples:**

```bash
# Development with local rules
daimyo --rules-path ./dev-rules serve --port 8001

# Production with system config
daimyo --config /etc/daimyo/config.toml serve --host 0.0.0.0

# Testing with temporary rules
daimyo -r /tmp/test-rules list-scopes

# Docker deployment
docker run -v /app/config:/config -v /app/rules:/rules daimyo \
  daimyo --config /config/settings.toml --rules-path /rules serve
```

**Note:** These are global options and must appear before the command name. For example:
- Correct: `daimyo --config myconfig.toml serve`
- Wrong: `daimyo serve --config myconfig.toml`

### Configuration Parameters

All configuration parameters with their defaults and descriptions:

#### Rules Directory

- **`rules_path`** (default: `".daimyo/rules"`)
  - Path to the directory containing scope definitions
  - Can be overridden via CLI (`--rules-path`), environment variable (`DAIMYO_RULES_PATH`), or discovered from standard locations
  - See [Rules Directory Discovery](#rules-directory-discovery) for precedence order
  - Environment variable: `DAIMYO_RULES_PATH`

#### Logging

- **`console_log_level`** (default: `"WARNING"`)
  - Log level for console output: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - Environment variable: `DAIMYO_CONSOLE_LOG_LEVEL`

- **`file_log_level`** (default: `"INFO"`)
  - Log level for file output: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
  - Environment variable: `DAIMYO_FILE_LOG_LEVEL`

- **`log_file`** (default: `"logs/daimyo.log"`)
  - Path to the main log file
  - Environment variable: `DAIMYO_LOG_FILE`

- **`log_json_file`** (default: `"logs/daimyo.jsonl"`)
  - Path to the JSON-formatted log file
  - Environment variable: `DAIMYO_LOG_JSON_FILE`

#### Scope Resolution

- **`max_inheritance_depth`** (default: `10`, range: `1-100`)
  - Maximum depth for scope inheritance chain to prevent infinite loops
  - Environment variable: `DAIMYO_MAX_INHERITANCE_DEPTH`

#### Remote Server (Federation)

- **`master_server_url`** (default: `""`)
  - URL of master server for scope federation (e.g., `"http://master.example.com:8000"`)
  - Leave empty to disable federation
  - Environment variable: `DAIMYO_MASTER_SERVER_URL`

- **`remote_timeout_seconds`** (default: `5`, range: `1-60`)
  - Timeout in seconds for remote server requests
  - Environment variable: `DAIMYO_REMOTE_TIMEOUT_SECONDS`

- **`remote_max_retries`** (default: `3`, range: `0-10`)
  - Maximum number of retry attempts for failed remote requests
  - Environment variable: `DAIMYO_REMOTE_MAX_RETRIES`

#### REST API Server

- **`rest_host`** (default: `"0.0.0.0"`)
  - Host address to bind the REST API server
  - Environment variable: `DAIMYO_REST_HOST`

- **`rest_port`** (default: `8000`, range: `1-65535`)
  - Port number for the REST API server
  - Environment variable: `DAIMYO_REST_PORT`

#### MCP Server

- **`mcp_transport`** (default: `"stdio"`, options: `"stdio"`, `"http"`)
  - Transport type for MCP server
  - `stdio`: Standard input/output (for CLI integrations)
  - `http`: HTTP server (for HTTP-based integrations)
  - Environment variable: `DAIMYO_MCP_TRANSPORT`

- **`mcp_host`** (default: `"0.0.0.0"`)
  - Host address to bind the MCP server when using HTTP transport
  - Only applies when `mcp_transport="http"`
  - Environment variable: `DAIMYO_MCP_HOST`

- **`mcp_port`** (default: `8001`, range: `1-65535`)
  - Port number for the MCP server when using HTTP transport
  - Only applies when `mcp_transport="http"`
  - Environment variable: `DAIMYO_MCP_PORT`

- **`default_scope`** (default: `""`)
  - Default scope name to use when `scope_name` parameter is not provided in MCP tools
  - When set, `get_rules()`, `get_category_index()`, and `apply_scope_rules()` can be called without specifying a scope
  - Empty string means no default (scope_name is required)
  - Environment variable: `DAIMYO_DEFAULT_SCOPE`

#### Markdown Formatting

- **`rules_markdown_prologue`** (default: `""`)
  - Text to prepend to markdown rules output
  - Supports Jinja2 templates with scope and config context
  - Available variables: `scope.name`, `scope.description`, `scope.tags`, config variables
  - Useful for adding headers or metadata to responses
  - Example: `"# Rules for {{ scope.name }}"`
  - Environment variable: `DAIMYO_RULES_MARKDOWN_PROLOGUE`

- **`rules_markdown_epilogue`** (default: `""`)
  - Text to append to markdown rules output
  - Supports Jinja2 templates with scope and config context
  - Available variables: `scope.name`, `scope.description`, `scope.tags`, config variables
  - Useful for adding footers or closing metadata
  - Example: `"Contact {{ TEAM_NAME | default('the team') }}"`
  - Environment variable: `DAIMYO_RULES_MARKDOWN_EPILOGUE`

- **`index_markdown_prologue`** (default: `""`)
  - Text to prepend to markdown category index output
  - Supports Jinja2 templates with scope and config context
  - Available variables: `scope.name`, `scope.description`, `scope.tags`, config variables
  - Environment variable: `DAIMYO_INDEX_MARKDOWN_PROLOGUE`

- **`index_markdown_epilogue`** (default: `""`)
  - Text to append to markdown category index output
  - Supports Jinja2 templates with scope and config context
  - Available variables: `scope.name`, `scope.description`, `scope.tags`, config variables
  - Environment variable: `DAIMYO_INDEX_MARKDOWN_EPILOGUE`

- **`default_category_description`** (default: `"These rules apply at all times"`)
  - Default description used when a category has no 'when' field and no parent to inherit from
  - Supports Jinja2 templates with scope and category context
  - Available variables: `category.key`, `scope.name`, `scope.description`, `scope.tags`, config variables
  - Example: `"Rules for {{ category.key }} in {{ scope.name }}"`
  - Falls back to hardcoded default on template errors
  - Environment variable: `DAIMYO_DEFAULT_CATEGORY_DESCRIPTION`

- **`commandments_xml_tag`** (default: `""`)
  - XML tag name to wrap commandment rules
  - Example: `"system-reminder"` produces `<system-reminder>rule</system-reminder>`
  - Empty string disables wrapping
  - Environment variable: `DAIMYO_COMMANDMENTS_XML_TAG`

- **`suggestions_xml_tag`** (default: `""`)
  - XML tag name to wrap suggestion rules
  - Example: `"system-suggestion"` produces `<system-suggestion>rule</system-suggestion>`
  - Empty string disables wrapping
  - Environment variable: `DAIMYO_SUGGESTIONS_XML_TAG`

- **`rules_categorized`** (default: `true`)
  - Whether to display rules in hierarchical categories
  - When `false`, rules are grouped under simple "Commandments" and "Suggestions" sections
  - Useful when categorization distracts language models from rule content
  - Environment variable: `DAIMYO_RULES_CATEGORIZED`

### Configuration File Example

```toml
[default]
# Rules directory configuration
rules_path = ".daimyo/rules"

# Logging configuration
console_log_level = "WARNING"
file_log_level = "INFO"
log_file = "logs/daimyo.log"
log_json_file = "logs/daimyo.jsonl"

# Scope resolution configuration
max_inheritance_depth = 10

# Remote server configuration
master_server_url = ""
remote_timeout_seconds = 5
remote_max_retries = 3

# REST API configuration
rest_host = "0.0.0.0"
rest_port = 8000

# MCP configuration
mcp_transport = "stdio"
mcp_host = "0.0.0.0"
mcp_port = 8001

# Markdown formatting configuration
rules_markdown_prologue = ""
rules_markdown_epilogue = ""
index_markdown_prologue = ""
index_markdown_epilogue = ""
default_category_description = "These rules apply at all times"
commandments_xml_tag = ""
suggestions_xml_tag = ""
rules_categorized = true

[development]
console_log_level = "DEBUG"
rest_port = 8001

[production]
console_log_level = "WARNING"
file_log_level = "WARNING"
```

### Environment Variables

Override any configuration parameter using environment variables with the `DAIMYO_` prefix:

```bash
# Configuration file location
export DAIMYO_CONFIG_FILE="/custom/config/settings.toml"

# Rules path
export DAIMYO_RULES_PATH="/custom/rules/path"

# Logging
export DAIMYO_CONSOLE_LOG_LEVEL="DEBUG"
export DAIMYO_FILE_LOG_LEVEL="INFO"

# Server federation
export DAIMYO_MASTER_SERVER_URL="http://master.example.com:8000"

# REST API
export DAIMYO_REST_HOST="127.0.0.1"
export DAIMYO_REST_PORT="9000"

# MCP Server
export DAIMYO_MCP_TRANSPORT="http"
export DAIMYO_MCP_HOST="0.0.0.0"
export DAIMYO_MCP_PORT="8001"
```

**Configuration Discovery Variables:**

- `DAIMYO_CONFIG_FILE`: Override the configuration file location (takes precedence over default discovery)
- `DAIMYO_RULES_PATH`: Override the rules directory location (takes precedence over config file setting)

## Examples

The `example-daimyo-rules/` directory contains working examples demonstrating best practices:

### python-general

**Parent:** None (base scope)

Foundation scope demonstrating proper category organization:

- **Universal categories**: `general`, `security`, `development.coding.python.implementation`, `development.coding.python.quality`, `development.coding.python.security`
  - Apply across all scopes when writing Python code
  - This scope provides mandatory rules for these universal categories
  - Defined in **commandments.yml**
- **Conditional categories**: `development.coding.python.testing`, `development.coding.python.documentation`
  - Apply across all scopes only when performing specific activities
  - This scope provides recommended rules for these universal categories
  - Defined in **suggestions.yml**
- **Aggregator categories**: `development.coding`, `development.coding.python`
  - Marked with "DO NOT USE DIRECTLY" warnings
  - Provide hierarchical organization without forcing over-fetching

**Key patterns demonstrated:**

- Separation of universal vs conditional categories
- Top-level `security` category for critical security mindset
- Clear "when" descriptions stating applicability
- Actionable, specific rules (not vague guidelines)

### team-backend

**Parent:** `python-general`

Team-specific scope demonstrating use of domain-specific categories:

- **Domain-specific categories**: `development.domain_specific.web_api`, `development.domain_specific.web_api.security`, `development.domain_specific.database`
  - Universal rules for backend development contexts
  - Defined in **commandments.yml**
- **Lifecycle categories**: `development.lifecycle.deployment`, `development.lifecycle.monitoring`
  - Phase-specific recommendations
  - Defined in **suggestions.yml**
- **Appending to parent**: Uses `+development.coding.python.testing` to extend parent's testing rules

**Key patterns demonstrated:**

- Domain-specific vs language-specific separation
- Lifecycle phase organization
- Using `+` prefix to append suggestions from parent scope
- Security as both commandments (mandatory) and domain-specific rules

### python-fastapi

**Parent:** `python-general`

Framework-specific scope demonstrating use of architecture pattern categories:

- **Architecture pattern categories**: `development.architecture_patterns.fastapi.*`
  - Marked with "ONLY apply when implementing FastAPI applications"
  - Emphasizes conditional nature with bold warnings
  - Includes routing, async operations, dependencies, performance, testing
- **Clear conditional boundaries**: All categories explicitly state they ONLY apply when using FastAPI

**Key patterns demonstrated:**

- Architecture patterns as conditional categories
- Consistent naming: `development.architecture_patterns.{framework}.{aspect}`
- Bold "ONLY apply when..." warnings to prevent misapplication
- Separating mandatory patterns (commandments) from optimization suggestions

### project-api

**Parents:** `[team-backend, python-fastapi]` (multiple inheritance)

Project-specific scope demonstrating practical composition:

- **Multiple parent inheritance**: Inherits from both team and framework scopes
- **Project-specific overrides**: Refines parent rules for specific project requirements
  - Example: Mandates UUID v4, RFC 7807 errors, request ID tracing
- **Appending to multiple parent categories**:
  - `+development.coding.python.testing` (extends both parents' testing rules)
  - `+development.architecture_patterns.fastapi.performance` (adds project-specific performance targets)
- **New project categories**: `development.lifecycle.review` for code review checklist

**Key patterns demonstrated:**

- Composing team rules + framework rules + project specifics
- Priority-based merging (team-backend = first parent = higher priority)
- Using `+` prefix to append to inherited suggestions
- Project-specific enforcement levels (e.g., authentication requirements)
- Practical combination of universal, conditional, and domain-specific rules

**Hierarchy summary:**

```text
project-api (project-level specifics)
  ├─ team-backend (context: web API development, databases)
  │   └─ python-general (context: Python development)
  └─ python-fastapi (context: FastAPI framework)
      └─ python-general (context: Python development)
```

**To explore these examples:**

```bash
# View category index for any scope
daimyo show python-general

# See merged rules with inheritance
curl http://localhost:8000/api/v1/scopes/project-api/rules

# Filter by specific categories
curl "http://localhost:8000/api/v1/scopes/project-api/rules?categories=development.coding.python.testing,development.domain_specific.web_api"
```

## Advanced Topics

### Multiple Parent Inheritance

```yaml
parents:
  - high-priority
  - low-priority
```

**Commandments**: All rules from all parents are combined (additive)

**Suggestions**: First parent wins in conflicts; use `+` prefix to append instead of replace

### Server Federation

Configure a master server for distributed scope management:

```bash
export DAIMYO_MASTER_SERVER_URL="http://master.example.com:8000"
```

The system will:

1. Look for scopes locally
2. Look for scopes on the master server
3. Merge both if found in both locations (local extends remote)

### Scope Sharding

The same scope name can exist on both master server and locally. When both exist, they are merged with the remote version as the base and the local version extending it.

### Template Rendering in Federated Deployments

**Important:** In federated deployments, templates are **always rendered by the requesting instance**, not by the master server.

When a subordinate instance fetches scopes from a master server:

1. **Master returns raw templates**: The master server returns unrendered templates with Jinja2 syntax intact (using `debug=true` internally)
2. **Subordinate renders with its own context**: The requesting instance renders templates using its own:
   - Configuration variables (from its `settings.toml` and environment)
   - Enabled plugins (git context, filesystem info, custom plugins)
   - Scope metadata and tags

**Why this matters:**

- **Different contexts per instance**: Each subordinate may have different plugins, variables, and configuration
- **Workspace-specific rendering**: Templates like `{{ git_branch }}` or `{{ project_name }}` resolve correctly for each workspace
- **Consistent rule logic, variable deployment**: Master defines rule templates once; each instance applies them with local context

**Example:**

Master server defines:

```yaml
python.deployment:
  ruleset:
    - Deploy to {{ DEPLOYMENT_REGION | default('us-east-1') }}
    - Notify {{ TEAM_SLACK | default('#deployments') }}
```

Subordinate A (with `DEPLOYMENT_REGION=eu-west-1`, `TEAM_SLACK=#eu-team`): Renders as "Deploy to eu-west-1" and "Notify #eu-team"

Subordinate B (with `DEPLOYMENT_REGION=us-west-2`, `TEAM_SLACK=#us-team`): Renders as "Deploy to us-west-2" and "Notify #us-team"

This architecture enables centralized rule management with decentralized context, allowing each workspace to maintain its own identity while following common organizational standards.

### Markdown formatting

Rules are typically rendered in Markdown format. LLMs may take advantage of certain formatting features such as emphasis or code fragments, so feel free to use these when writing rules.

### Jinja2 Templates

Rules, category descriptions, prologues, epilogues, and the default category description support Jinja2 templates for dynamic content based on configuration and scope metadata.

#### Available Template Variables

Templates can access:

- **Configuration**: All `DAIMYO_*` environment variables and settings from `config/settings.toml`
- **Scope metadata**: `scope.name`, `scope.description`, `scope.tags`, `scope.sources`
- **Category info**: `category.key`, `category.when` (in rule text only)

#### Basic Example

**Configuration** (`config/settings.toml`):

```toml
[default]
TEAM_NAME = "Backend Team"
SLACK_CHANNEL = "#backend"
```

**Rules with templates** (`commandments.yml`):

```yaml
python.monitoring:
  when: "When monitoring {{ scope.name }} in {{ scope.tags.env | default('dev') }}"
  ruleset:
    - "Alert {{ TEAM_NAME }} via {{ SLACK_CHANNEL }}"
    - "Log level: {{ LOG_LEVEL }}"
```

**Rendered output** (assuming `scope.tags.env = "production"`):

```markdown
## python.monitoring
*When monitoring my-service in production*
- **MUST**: Alert Backend Team via #backend
- **MUST**: Log level: INFO
```

#### Best Practices

**Always use the `default` filter** for optional variables:

```yaml
- "Use {{ MY_VAR | default('fallback_value') }} for configuration"
```

**Conditionals**:

```yaml
- "{% if scope.tags.env == 'prod' %}Use strict security{% else %}Use standard security{% endif %}"
```

**Multiple variables**:

```yaml
- "Team {{ scope.tags.team }} deploys to {{ scope.tags.region }}"
```

#### Error Handling

Daimyo handles template errors gracefully. When templates fail to render (missing context variables, unavailable filters/tests), the system:

- Removes the failed element from the main response body
- Collects failure information
- Reports failures in a separate section (minimal format for LLMs)

**JSON/YAML responses** include a `template_failures` field:

```json
{
  "metadata": { ... },
  "commandments": { ... },
  "suggestions": { ... },
  "template_failures": [
    {
      "element_type": "rule",
      "element_identifier": "python.web rule #2",
      "template_text": "Use {{ UNDEFINED_VAR }} ...",
      "error_message": "'UNDEFINED_VAR' is undefined",
      "variable_name": "UNDEFINED_VAR"
    }
  ]
}
```

**Markdown responses** include a compact failures section wrapped in `<ignore-failed-template>` tags:

````markdown
<ignore-failed-template>
## Template Failures

**python.web rule #2**: `UNDEFINED_VAR` undefined
```
Use {{ UNDEFINED_VAR }} for configuration
```

**python.testing rule #5**: `TEST_FRAMEWORK` undefined
```
Use {{ TEST_FRAMEWORK }} for all tests
```

</ignore-failed-template>
````

Failed elements are **removed** from the main response body and only appear in this diagnostic section. The `<ignore-failed-template>` tags provide a clear signal to LLMs to completely ignore this information. The format is concise while still showing the original template content for debugging.

#### Use Cases

**Environment-aware rules**:

```yaml
python.deployment:
  when: "When deploying to {{ scope.tags.region }}"
  ruleset:
    - "Deploy to {{ scope.tags.region }} region"
    - "{% if scope.tags.env == 'production' %}Require manual approval{% endif %}"
    - "Notification: {{ SLACK_DEPLOY_CHANNEL | default('#deployments') }}"
```

**Team-specific rules**:

```yaml
code-review:
  when: "When reviewing code for {{ TEAM_NAME }}"
  ruleset:
    - "Review in {{ CODE_REVIEW_TOOL | default('SonarQube') }}"
    - "Require approval from {{ scope.tags.team }} lead"
```

**Templated prologues and epilogues**:

```toml
[default]
rules_markdown_prologue = '''
# Rules for {{ scope.name }}
*{{ scope.description }}*

These rules are {{ "critical" if scope.tags.env == "production" else "recommended" }}.
'''

rules_markdown_epilogue = "Questions? Contact {{ TEAM_NAME | default('the team') }} via {{ SLACK_CHANNEL | default('#general') }}"

default_category_description = "Rules for {{ category.key }} - applies in {{ scope.name }}"
```

## Plugin System

Daimyo supports plugins (bugyo - 奉行) that extend functionality through callback hooks.

### Using Plugins

#### 1. Install a Plugin

Plugins are installed via pip:

```bash
pip install daimyo-example-plugin
```

#### 2. Enable Plugins

Edit `.daimyo/config/settings.toml`:

```toml
enabled_plugins = [
    "git.*",         # Enable all git plugins
    "fs.*",          # Enable all filesystem plugins
    "example.*",     # Enable all plugins with 'example' prefix
    "git.context",   # Enable specific plugin only
]
```

Wildcard patterns supported:

- `"example.*"` - Enable all plugins starting with "example."
- `"example.context"` - Enable specific plugin only

Note: The `"*"` wildcard to enable all plugins is not supported. You must explicitly specify plugin patterns.

#### 3. Running plugins

Once enabled, plugin callbacks are called on different events. For instance, when providing additional context to the templating system:

```yaml
python.web:
  when: When writing Python web code
  ruleset:
    - Use custom variable: {{ custom_var }}
```

### Official Plugins

Daimyo provides official plugins for common use cases. See the [Plugin Catalog](plugins/README.md) for details.

### Creating Plugins

Each plugin has its own entry point and inherits from a specialized base class depending on its purpose.

#### Context Provider Plugins

Provide template variables for Jinja2 templates:

`my_plugin.py`:

```python
from daimyo.domain import ContextProviderPlugin

class MyPlugin(ContextProviderPlugin):
    @property
    def name(self) -> str:
        return "myplugin.context"

    @property
    def description(self) -> str:
        return "Provides custom context variables"

    def is_available(self) -> bool:
        """Check if plugin can run in current environment."""
        return True

    def get_context(self, scope) -> dict:
        """Provide template variables."""
        return {
            "my_var": "my_value",
            "git_branch": "main",
        }
```

`pyproject.toml`:

```toml
[project.entry-points."daimyo.plugins"]
"myplugin.context" = "my_plugin:MyPlugin"
```

Install and enable:

```bash
pip install -e .
```

Then add to `config/settings.toml`:

```toml
enabled_plugins = ["myplugin.*"]
```

#### Filter Provider Plugins

Provide custom Jinja2 filters and tests:

`my_filters.py`:

```python
from daimyo.domain import FilterProviderPlugin
import os.path

class MyFiltersPlugin(FilterProviderPlugin):
    @property
    def name(self) -> str:
        return "myplugin.filters"

    @property
    def description(self) -> str:
        return "Provides custom Jinja2 filters and tests"

    def is_available(self) -> bool:
        return True

    def get_filters(self) -> dict:
        """Provide custom Jinja2 filters."""
        return {
            "uppercase": lambda s: s.upper(),
            "quote": lambda s: f'"{s}"',
        }

    def get_tests(self) -> dict:
        """Provide custom Jinja2 tests."""
        return {
            "file_exists": lambda path: os.path.exists(path),
            "git_repo": lambda path: os.path.exists(os.path.join(path, ".git")),
        }
```

Use in templates:

```yaml
python.web:
  when: When writing Python web code
  ruleset:
    - Name must be {{ package_name | uppercase }}
    - |
      {% if "." is file_exists %}
      Include tests
      {% endif %}
```

#### Plugin Entry Points

Register plugins in **pyproject.toml**:

```toml
[project.entry-points."daimyo.plugins"]
"myplugin.context" = "my_plugin:MyPlugin"
"myplugin.filters" = "my_filters:MyFiltersPlugin"
```

Each plugin has its own entry point for independent discovery and enablement.

### Deployment Pattern: Workspace-Local Instance

A common deployment pattern is running a daimyo instance that:

- Has no local rules directory (or minimal workspace-specific rules)
- References a master daimyo server via `DAIMYO_MASTER_SERVER_URL` for shared organizational rules
- May have workspace-specific plugins installed for context (e.g., git metadata, local filesystem info)

This pattern is useful for:

- **Consistent org-wide rules** with workspace-specific context
- **Reduced duplication** across projects
- **Easier centralized rule management** - update rules once on the master server

Example configuration for a workspace-local instance:

```toml
[default]
rules_path = ".daimyo/rules"  # Empty or minimal local rules
master_server_url = "http://rules.company.com:8000"
enabled_plugins = ["git.*", "fs.*"]
```

In Japanese tradition, this role is called "rusuiyaku" (留守居役, "caretaker") - representing the master in the local workspace.

**Template Rendering:** Workspace-local instances render templates with their own local context (plugins, configuration, environment variables). The master server provides raw template definitions, and each workspace-local instance applies its own values. See [Template Rendering in Federated Deployments](#template-rendering-in-federated-deployments) for details.

## Development

### Running Tests

```bash
pip install -e ".[dev]"
pytest
pytest --cov=daimyo
```

### Code Quality

```bash
mypy daimyo
ruff check daimyo
ruff format daimyo
```

## License

MIT
