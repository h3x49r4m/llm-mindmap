---
name: tdd-enforce
description: Ensures Test-Driven Development (TDD) workflow is followed throughout the development process
version: 1.0.0
category: development-process
---

# TDD Enforcement Skill

Ensures Test-Driven Development (TDD) workflow is followed throughout the development process.

## Usage

```
/tdd-enforce
```

## What It Does

### 1. Test-First Lock
Prevents implementation without corresponding tests:
- Checks if test file exists before allowing implementation file creation
- Requires test to fail first (red phase)
- Only allows minimal implementation to pass test (green phase)
- Requires refactoring step (refactor phase)

### 2. Test Coverage Gates
Enforces coverage thresholds (configurable in `config.json`):
```json
{
  "tddEnforce": {
    "coverageThresholds": {
      "lines": 90,
      "branches": 80,
      "functions": 90,
      "statements": 90
    },
    "criticalCoverage": {
      "integrationFlow": 100,
      "safetyConstraints": 100
    }
  }
}
```

Default thresholds:
- Component coverage: ≥90% lines, ≥80% branches
- Integration flow coverage: 100%
- Safety constraint coverage: 100%
- Blocks commits if coverage drops below thresholds

### 3. Red-Green-Refactor Cycle Verification
Validates each step of the TDD cycle:
- Detects test creation (no matching implementation)
- Verifies test fails (red state confirmed)
- Detects minimal implementation
- Verifies test passes (green state achieved)
- Detects refactoring changes (without new tests)

### 4. Test Structure Validation
Ensures tests follow TDD best practices:
- Arrange-Act-Assert structure
- Single assertion per test
- Descriptive test names
- Independence between tests
- No test interdependencies

### 5. Implementation Restriction
Enforces test-first workflow:
- Cannot create implementation file without corresponding test file
- Cannot add new function without test
- Cannot modify existing behavior without updating test

### 6. CI Integration
Pipeline checks for automated enforcement:
- All tests pass before merge
- Coverage thresholds met
- TDD cycle steps validated in commit history
- Architecture compliance verified

### 7. Coding Principles Compliance
Enforces coding quality principles from refactoring best practices:
- **Magic Literals Extraction**: Detects hardcoded numbers/strings, requires named constants
- **Long Functions Decomposition**: Validates function length, complexity, and parameter count
- **Poor Naming Improvements**: Ensures descriptive, self-documenting variable/function names
- **Dead Code Elimination**: Detects unused imports, variables, functions, and classes
- **Complex Conditionals Reduction**: Simplifies nested if/else statements and boolean expressions
- **Code Smells Detection**: Identifies god functions, feature envy, data clumps, primitive obsession
- **Duplicate Code Detection**: Finds identical or similar code blocks across the project

These principles are enforced during the green and refactor phases of the TDD cycle to ensure code quality from the start.

## Output Format

```
TDD Compliance Report
=====================

Overall Score: 85% (17/20 checks passed)

RED-GREEN-REFACTOR CYCLE
-------------------------
✓ Test Creation Phase (PASS)
✓ Test Failure (Red) (PASS)
✓ Minimal Implementation (Green) (PASS)
✗ Refactoring Phase (FAIL) - No refactoring detected after green

TEST COVERAGE
-------------
Component Coverage: 92% (Required: ≥90%) ✓
Integration Flow Coverage: 100% (Required: 100%) ✓
Safety Constraint Coverage: 95% (Required: 100%) ✗
Overall Coverage: 89% (Required: ≥90%) ✗

TEST STRUCTURE
--------------
✓ Arrange-Act-Assert Pattern (PASS)
✓ Single Assertion Per Test (PASS)
✓ Descriptive Test Names (PASS)
✓ Test Independence (PASS)
✗ No Test Interdependencies (FAIL) - Found 2 dependent tests

IMPLEMENTATION RESTRICTION
---------------------------
✓ All implementations have tests (PASS)
✓ All functions are tested (PASS)
✗ Behavior changes have test updates (FAIL) - Modified goal_engine without test update

CODING PRINCIPLES
-----------------
✓ Magic Literals (PASS) - No hardcoded numbers/strings detected
✗ Long Functions (FAIL) - process_data exceeds 50 lines (67 lines)
✓ Poor Naming (PASS) - All names are descriptive
✗ Dead Code (FAIL) - Found 2 unused imports in utils.py
✓ Complex Conditionals (PASS) - No deeply nested conditionals
✗ Code Smells (FAIL) - God function detected in orchestrator.py
✓ Duplicate Code (PASS) - No duplicate code blocks found

RECURSION AND INFINITE LOOPS
-----------------------------
✗ Recursive function detected (FAIL) - Function calls itself
✓ All loops have explicit termination (PASS)
✓ Loop bounds defined with constants (PASS)
✗ Infinite loop pattern detected (FAIL) - while(true) found

VIOLATIONS
----------
1. Refactoring Phase (evo/src/decision_engine.rs)
   No refactoring detected after green phase
   Suggested: Review and refactor for code quality

2. Safety Constraint Coverage (evo/tests/safety_test.rs)
   Coverage: 95% (Required: 100%)
   Missing: storage_limit_enforcement
   Suggested: Add test for storage limit enforcement

3. Test Interdependencies (evo/tests/integration_test.rs)
   Found 2 dependent tests: test_mode_selection, test_handler_routing
   Suggested: Make tests independent with proper setup/teardown

4. Behavior Changes (evo/src/goal_engine.rs)
   Modified goal_engine without test update
   Suggested: Update evo/tests/goal_engine_test.rs to reflect changes

5. Recursive Function (evo/src/tree_utils.rs)
   Function traverseTree calls itself recursively
   Suggested: Convert to iterative solution using stack or queue

6. Infinite Loop (evo/src/event_loop.rs)
   Pattern while(true) detected at line 42
   Suggested: Add explicit condition and timeout limit
   Modified goal_engine without test update
   Suggested: Update evo/tests/goal_engine_test.rs to reflect changes

CRITICAL VIOLATIONS: 2 (Build will FAIL)
WARNINGS: 2

TDD CYCLE HISTORY
-----------------
Commit 28d8bfb: Test created → Test failed → Implementation → Test passed ✓
Commit a61cdf0: Test created → Test failed → Implementation → Test passed → Refactored ✓
Commit 4de2892: Test created → Test failed → Implementation → Test passed ✗ (no refactoring)
```

## Enforcement Rules

### Recursion Detection

**AST Analysis:**
- Detect direct recursion: function calling itself
- Detect indirect recursion: mutual recursion between functions
- Detect tail recursion: still prohibited, use iteration

**Pattern Matching:**
```typescript
// Direct recursion detected
function factorial(n) {
  return n * factorial(n - 1)
}

// Indirect recursion detected
function isEven(n) { return isOdd(n - 1) }
function isOdd(n) { return isEven(n - 1) }
```

**Enforcement:**
```
Attempting to commit: src/utils/tree.ts
VIOLATION: Recursive function detected
  Function: traverse(node)
  Line: 12
  Calls: traverse(node.left), traverse(node.right)
ACTION: Convert to iterative solution using stack/queue
```

### Infinite Loop Detection

**Pattern Matching:**
- `while(true)` - Always infinite
- `while(1)` - Always infinite
- `for(;;)` - Always infinite
- Unbounded loops without termination conditions

**Enforcement:**
```
Attempting to commit: src/core/event_loop.ts
VIOLATION: Infinite loop detected
  Pattern: while(true)
  Line: 42
ACTION: Add explicit condition and maximum iteration limit
```

### Loop Bounding Requirements

**Required for all loops:**
1. Explicit termination condition
2. Maximum iteration limit or timeout
3. Early exit on error/timeout

**Examples:**
```typescript
// ✅ Bounded loop
const MAX_ITERATIONS = 1000
const TIMEOUT_MS = 5000
const startTime = Date.now()

while (!isDone() && iterations < MAX_ITERATIONS && (Date.now() - startTime) < TIMEOUT_MS) {
  processItem()
  iterations++
}
```

### File Creation
```
Attempting to create: evo/src/component.rs
VIOLATION: No corresponding test file evo/tests/component_test.rs exists
ACTION: Create test file first, then implement
```

### Function Addition
```
Attempting to add function: new_capability
VIOLATION: No test for new_capability found
ACTION: Add test first, then implement function
```

### Behavior Modification
```
Attempting to modify: goal_engine.evaluate
VIOLATION: Test not updated to reflect new behavior
ACTION: Update test, then modify implementation
```

### Magic Literals Detection
**Pattern Matching:**
- Hardcoded numbers (excluding 0, 1, -1)
- Hardcoded strings (excluding empty string)
- Repeated literals (occurs 2+ times)

**Enforcement:**
```
Attempting to commit: src/processor.py
VIOLATION: Magic literal detected
  Literal: 3.14159 at line 15
  Suggested: Define constant PI = 3.14159
ACTION: Extract to named constant
```

### Long Functions Detection
**Thresholds (configurable):**
- `max_lines`: 50 (default)
- `max_complexity`: 10 (default)
- `max_parameters`: 5 (default)
- `max_nesting_depth`: 4 (default)

**Enforcement:**
```
Attempting to commit: src/processor.py
VIOLATION: Function exceeds length threshold
  Function: process_complex_data (67 lines, limit: 50)
  Complexity: 12 (limit: 10)
  Parameters: 6 (limit: 5)
  Nesting depth: 5 (limit: 4)
ACTION: Decompose into smaller functions with single responsibility
```

### Poor Naming Detection
**Validation Rules:**
- Minimum name length: 3 characters
- Forbidden names: temp, data, info, obj, var, item
- Enforce camelCase for functions/variables (configurable)
- Enforce PascalCase for classes (configurable)
- Descriptive, self-documenting names required

**Enforcement:**
```
Attempting to commit: src/processor.py
VIOLATION: Poor naming detected
  Variable: 'temp' at line 23 (too generic)
  Function: 'calc' at line 45 (too abbreviated)
ACTION: Use descriptive names: 'temp_data', 'calculate_metric'
```

### Dead Code Detection
**Analysis:**
- Unused imports across all files
- Unused variables and parameters
- Unused functions, classes, and methods
- Unreachable code blocks

**Enforcement:**
```
Attempting to commit: src/processor.py
VIOLATION: Dead code detected
  Unused import: 'json' (line 5)
  Unused variable: 'counter' (line 32)
  Unused function: 'legacy_handler' (line 78)
ACTION: Remove unused code to improve maintainability
```

### Complex Conditionals Detection
**Pattern Matching:**
- Nested if/else statements (>3 levels)
- Complex boolean expressions (>3 conditions)
- Multiple consecutive if statements (can use switch/case)

**Enforcement:**
```
Attempting to commit: src/processor.py
VIOLATION: Complex conditional detected
  Nested if/else depth: 5 (limit: 3)
  Location: process_validation (line 45-67)
ACTION: Use guard clauses, early returns, or switch/case
```

### Code Smells Detection
**Anti-patterns:**
- **God Functions**: Functions with too many responsibilities (>200 lines, >15 complexity)
- **Feature Envy**: Functions that use another object's data more than their own
- **Data Clumps**: Variables that appear together frequently (extract to object)
- **Primitive Obsession**: Using primitives instead of domain objects

**Enforcement:**
```
Attempting to commit: src/orchestrator.py
VIOLATION: Code smell detected
  Type: God Function
  Function: handle_all_operations (250 lines, complexity: 20)
ACTION: Split into smaller, focused functions with single responsibility
```

### Duplicate Code Detection
**Analysis:**
- Identical code blocks (100% match)
- Similar code blocks (≥80% similarity)
- Minimum 5 lines for duplicate consideration
- Ignores test files (configurable)

**Enforcement:**
```
Attempting to commit: src/processor.py
VIOLATION: Duplicate code detected
  Similarity: 95% (15 lines)
  Locations:
    - src/processor.py:45-60
    - src/validator.py:78-93
ACTION: Extract to reusable function
```

## Exit Codes

- `0` - All TDD checks passed
- `1` - Critical violations found (build should fail)
- `2` - Warnings only (build can continue)
- `3` - TDD cycle incomplete (missing red/green/refactor steps)

## CI Integration

Add to your CI pipeline:

```yaml
- name: TDD Enforcement
  run: |
    iflow /tdd-enforce
    if [ $? -eq 1 ]; then
      echo "TDD violations detected. Fix before merging."
      exit 1
    fi
```

## IDE Integration

### VS Code
Create `.vscode/settings.json`:
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true
  },
  "files.associations": {
    "*.test.ts": "typescript"
  }
}
```

### Vim/Neovim
Add to `.vimrc`:
```vim
autocmd BufWritePost *.test.ts :!tdd-enforce check %
```

### Real-Time Feedback

The skill provides real-time feedback during development:

**Red Phase Detection:**
- Monitors test file creation
- Validates test fails before implementation
- Alert: "Test must fail before implementation (TDD red phase)"

**Green Phase Detection:**
- Monitors implementation file creation
- Validates minimal implementation only
- Alert: "Implementation exceeds minimal required code"

**Refactor Phase Detection:**
- Monitors code changes after green phase
- Validates refactoring improves code quality
- Alert: "Refactoring step required (TDD refactor phase)"

**Integration with Watch Mode:**
```bash
# Run TDD enforcement in watch mode
/tdd-enforce watch
```

This monitors file changes and provides instant feedback on TDD compliance.

## Implementation Notes

This skill uses:
- Git history analysis to track TDD cycle progression
- AST parsing for structure validation
- Coverage analysis tools for threshold checking
- Dependency analysis for test independence verification
- File modification tracking for implementation restriction

## Best Practices

### TDD Workflow
1. Always write tests first
2. Ensure tests fail before implementation
3. Write minimal implementation to pass
4. Refactor after green phase
5. Keep tests independent and focused
6. Maintain high coverage (≥90% by default, configurable)
7. Update tests when behavior changes

### Code Quality Principles
8. Never use recursive algorithms - use iterative solutions
9. Always bound loops with explicit conditions and limits
10. Avoid while(true), for(;;), and infinite loops
11. Extract magic literals to named constants
12. Keep functions short (<50 lines, <10 complexity)
13. Use descriptive, self-documenting names
14. Remove unused imports, variables, and functions
15. Simplify complex conditionals with guard clauses
16. Avoid code smells: god functions, feature envy, data clumps
17. Eliminate duplicate code through extraction

### Naming Conventions
- Use camelCase for functions and variables
- Use PascalCase for classes and types
- Use UPPER_SNAKE_CASE for constants
- Minimum 3 characters for names
- Avoid abbreviations: use 'calculate' not 'calc'
- Avoid generic names: temp, data, info, obj, var, item

### Function Design
- Single responsibility: one function, one purpose
- Maximum 5 parameters (use objects for more)
- Maximum 4 levels of nesting
- Maximum cyclomatic complexity of 10
- Maximum 50 lines of code
- Pure functions when possible (no side effects)

### Code Organization
- Group related code into modules/packages
- Extract duplicate code to shared functions
- Use domain objects instead of primitives
- Keep files focused and coherent
- Organize imports: stdlib, third-party, local

## Iterative Over Recursive

**Why Iteration:**
- Predictable memory usage (no stack growth)
- No stack overflow risk
- Better performance (no function call overhead)
- Easier to debug and test
- More resource-efficient

**Common Patterns:**

**Factorial:**
```typescript
// ❌ Recursive
function factorial(n) { return n <= 1 ? 1 : n * factorial(n-1) }

// ✅ Iterative
function factorial(n) {
  let result = 1
  for (let i = 2; i <= n; i++) result *= i
  return result
}
```

**Tree Traversal:**
```typescript
// ❌ Recursive
function traverse(node) {
  if (!node) return
  console.log(node.value)
  traverse(node.left)
  traverse(node.right)
}

// ✅ Iterative (stack-based)
function traverse(root) {
  const stack = [root]
  while (stack.length > 0) {
    const node = stack.pop()
    console.log(node.value)
    if (node.right) stack.push(node.right)
    if (node.left) stack.push(node.left)
  }
}
```

**DFS/BFS:**
```typescript
// ❌ Recursive DFS
function dfs(node, target) {
  if (!node) return false
  if (node.value === target) return true
  return dfs(node.left, target) || dfs(node.right, target)
}

// ✅ Iterative DFS
function dfs(root, target) {
  const stack = [root]
  while (stack.length > 0) {
    const node = stack.pop()
    if (node.value === target) return true
    if (node.right) stack.push(node.right)
    if (node.left) stack.push(node.left)
  }
  return false
}
```

## Property-Based Testing

The skill supports property-based testing for edge case coverage:

```json
{
  "tddEnforce": {
    "enablePropertyBasedTesting": true,
    "propertyTestFrameworks": ["hypothesis", "fast-check", "jsverify"]
  }
}
```

**Property Test Validation:**
- Ensures property tests exist for critical functions
- Validates property test coverage (≥80% of critical paths)
- Checks for invariant preservation
- Validates edge case generation

**Example Property Test Requirements:**
```python
# Required property tests for critical functions
@pytest.mark.parametrize("input, expected", property_test_cases)
def test_property_preserves_invariant(input, expected):
    result = function_under_test(input)
    assert invariant_holds(result)
```

## Configuration

### Coverage Thresholds

```json
{
  "tddEnforce": {
    "coverageThresholds": {
      "lines": 90,
      "branches": 80,
      "functions": 90,
      "statements": 90
    },
    "criticalCoverage": {
      "integrationFlow": 100,
      "safetyConstraints": 100
    }
  }
}
```

### Coding Principles Thresholds

```json
{
  "tddEnforce": {
    "codingPrinciples": {
      "magicLiterals": {
        "enabled": true,
        "minOccurrences": 2,
        "ignoreValues": [0, 1, -1, "", "null", "false", "true"],
        "extractNumbers": true,
        "extractStrings": true
      },
      "longFunctions": {
        "enabled": true,
        "maxLines": 50,
        "maxComplexity": 10,
        "maxParameters": 5,
        "maxNestingDepth": 4,
        "ignoreTestFiles": false
      },
      "poorNaming": {
        "enabled": true,
        "minNameLength": 3,
        "forbiddenNames": ["temp", "data", "info", "obj", "var", "item"],
        "enforceCamelCase": true,
        "enforcePascalCase": true,
        "enforceUpperSnakeCase": true
      },
      "deadCode": {
        "enabled": true,
        "checkUnusedImports": true,
        "checkUnusedVariables": true,
        "checkUnusedFunctions": true,
        "checkUnusedClasses": true,
        "ignoreUnderscored": true
      },
      "complexConditionals": {
        "enabled": true,
        "maxNestingDepth": 3,
        "maxBooleanConditions": 3,
        "suggestGuardClauses": true
      },
      "codeSmells": {
        "enabled": true,
        "detectGodFunctions": true,
        "detectFeatureEnvy": true,
        "detectDataClumps": true,
        "detectPrimitiveObsession": true,
        "godFunctionThreshold": {
          "maxLines": 200,
          "maxComplexity": 15
        }
      },
      "duplicateCode": {
        "enabled": true,
        "minSimilarityScore": 0.8,
        "minLinesForDuplicate": 5,
        "ignoreTestFiles": true,
        "ignoreComments": true,
        "ignoreWhitespace": true
      }
    }
  }
}
```

### Property-Based Testing

```json
{
  "tddEnforce": {
    "enablePropertyBasedTesting": true,
    "propertyTestFrameworks": ["hypothesis", "fast-check", "jsverify"],
    "propertyTestCoverageThreshold": 80
  }
}
```

### Recursive and Loop Enforcement

```json
{
  "tddEnforce": {
    "banRecursion": true,
    "allowTailRecursion": false,
    "banInfiniteLoops": true,
    "requireLoopBounds": true,
    "maxLoopIterations": 10000,
    "loopTimeoutMs": 5000
  }
}
```