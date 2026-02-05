---
name: typescript-validator
description: Validates TypeScript code by running type checking after creating or modifying React components. Use this skill after creating new components, modifying existing ones, or when the user asks to validate TypeScript. Catches type errors early before they cause runtime issues.
---

# TypeScript Validator Skill

## Overview

This skill validates TypeScript code by running the TypeScript compiler in type-check mode. Use it after creating or modifying React components to catch type errors early.

---

## When to Use

- After creating a new TypeScript/React component
- After modifying existing TypeScript files
- When user asks to "validate", "type check", or "check for errors"
- Before committing code changes
- After refactoring or moving files

---

## Process

### Step 1: Run Type Check

Execute TypeScript compiler in check-only mode:

```bash
cd frontend && npx tsc --noEmit
```

This validates all TypeScript files without generating output.

### Step 2: Analyze Errors

If errors are found, categorize them:

| Error Type | Example | Fix |
|------------|---------|-----|
| Missing import | `Cannot find module` | Add import statement |
| Type mismatch | `Type 'string' is not assignable to 'number'` | Fix type annotation |
| Missing prop | `Property 'X' is missing` | Add required prop or make optional |
| Undefined variable | `Cannot find name 'X'` | Import or define variable |
| Missing return type | `implicitly has return type 'any'` | Add explicit return type |

### Step 3: Fix Errors

For each error:
1. Navigate to the file and line number
2. Understand the context
3. Apply the appropriate fix
4. Re-run type check to verify

### Step 4: Validate Specific Files (Optional)

To check a specific file:

```bash
cd frontend && npx tsc --noEmit src/components/MyComponent.tsx
```

---

## Common Tiger ID Type Patterns

### Investigation Types
```typescript
import type {
  Investigation2State,
  Investigation2Match,
  Investigation2Phase
} from '../types/investigation2'
```

### Tiger Types
```typescript
import type { Tiger, TigerMatch, TigerFilters } from '../types'
```

### Component Props Pattern
```typescript
interface MyComponentProps {
  data: Tiger[]
  onSelect?: (tiger: Tiger) => void
  isLoading?: boolean
  className?: string
}
```

### API Response Pattern
```typescript
interface ApiResponse<T> {
  data: T
  error?: string
  meta?: { total: number; page: number }
}
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `npx tsc --noEmit` | Full project type check |
| `npx tsc --noEmit --watch` | Continuous type checking |
| `npx tsc --noEmit --skipLibCheck` | Skip node_modules checking |
| `npx tsc --listFiles` | List all files being checked |

---

## Integration with Workflow

After creating components with the `python-ui-frontend-engineer` agent:

1. Run `typescript-validator` skill to check for type errors
2. Fix any errors found
3. Run again to verify fixes
4. Proceed with testing

This ensures type safety before the code is tested or deployed.
