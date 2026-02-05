---
name: import-path-fixer
description: Automatically updates import paths when files are moved or renamed. Use this skill after reorganizing the codebase, moving components to new directories, or when import errors occur. Ensures all references stay in sync.
---

# Import Path Fixer Skill

## Overview

This skill updates import paths throughout the codebase when files are moved, renamed, or reorganized. It prevents broken imports and maintains codebase integrity during refactoring.

---

## When to Use

- After moving a component to a new directory
- After renaming a file or component
- When import errors appear after refactoring
- When user asks to "fix imports" or "update paths"
- During large-scale codebase reorganization

---

## Process

### Step 1: Identify the Change

Document what changed:

```markdown
**Change Type**: Move / Rename / Delete

**Original Location**: `src/components/OldPath/Component.tsx`
**New Location**: `src/components/NewPath/Component.tsx`

**Original Export Name**: `ComponentName`
**New Export Name**: `ComponentName` (unchanged)
```

### Step 2: Find All References

Search for imports of the moved file:

```bash
# Find all imports of the component
grep -rn "from.*OldPath/Component" frontend/src/
grep -rn "from.*OldPath'" frontend/src/

# Find barrel imports
grep -rn "import.*{.*ComponentName.*}.*from" frontend/src/
```

### Step 3: Update Import Paths

For each reference found:

```typescript
// Before (old path)
import { ComponentName } from '../components/OldPath/Component'
import { ComponentName } from '@/components/OldPath'

// After (new path)
import { ComponentName } from '../components/NewPath/Component'
import { ComponentName } from '@/components/NewPath'
```

### Step 4: Update Barrel Exports

If the component was exported from an index.ts:

```typescript
// Old index.ts - remove line
export { default as ComponentName } from './Component'

// New index.ts - add line
export { default as ComponentName } from './Component'
```

### Step 5: Verify All Imports

Run TypeScript to verify no broken imports:

```bash
cd frontend && npx tsc --noEmit
```

---

## Common Move Scenarios

### Scenario 1: Component to Sub-directory

```
Before: src/components/LargeComponent.tsx
After:  src/components/feature/LargeComponent.tsx

Find:   from '.*/LargeComponent'
        from '.*/components/LargeComponent'

Replace: from '.*/components/feature/LargeComponent'
         from '.*/components/feature'  (if barrel exported)
```

### Scenario 2: Consolidate Components

```
Before: src/components/common/Button.tsx
        src/components/common/Input.tsx
        src/components/common/Card.tsx

After:  src/components/ui/Button.tsx
        src/components/ui/Input.tsx
        src/components/ui/Card.tsx

Find all: from '.*/common'
Replace:  from '.*/ui'
```

### Scenario 3: Split Large File

```
Before: src/components/Investigation2ResultsEnhanced.tsx (800 lines)

After:  src/components/investigations/Investigation2ResultsEnhanced.tsx
        src/components/investigations/tabs/OverviewTab.tsx
        src/components/investigations/tabs/DetectionTab.tsx
        src/components/investigations/tabs/MatchingTab.tsx

Update parent imports and add internal imports to new files.
```

---

## Path Resolution Rules

### Relative Paths

```typescript
// Same directory
import { Sibling } from './Sibling'

// Parent directory
import { Parent } from '../Parent'

// Nested child
import { Child } from './children/Child'

// Two levels up
import { Ancestor } from '../../Ancestor'
```

### Alias Paths (if configured)

```typescript
// With @ alias (tsconfig paths)
import { Component } from '@/components/path'

// With src alias
import { Component } from 'src/components/path'
```

---

## Tiger ID File Structure Reference

```
frontend/src/
├── components/
│   ├── common/           # Shared UI components
│   ├── layout/           # Layout components (Header, Sidebar)
│   ├── investigations/   # Investigation workflow components
│   │   ├── progress/     # Progress tracking
│   │   ├── results/      # Results display
│   │   └── tabs/         # Tab content
│   ├── tigers/           # Tiger management
│   ├── discovery/        # Discovery pipeline
│   ├── dashboard/        # Dashboard widgets
│   ├── facilities/       # Facility management
│   └── verification/     # Verification queue
├── pages/                # Page components
├── hooks/                # Custom hooks
├── context/              # React context
├── app/                  # RTK Query API
├── types/                # TypeScript types
├── utils/                # Utility functions
└── features/             # Redux slices
```

---

## Bulk Update Commands

### Using sed (Unix)

```bash
# Replace path in all .tsx files
find frontend/src -name "*.tsx" -exec sed -i 's|from.*OldPath|from "../NewPath|g' {} \;
```

### Using grep + manual

```bash
# Find files needing updates
grep -rl "OldPath" frontend/src/ --include="*.tsx"

# Count occurrences
grep -rc "OldPath" frontend/src/ --include="*.tsx" | grep -v ":0"
```

---

## Verification Checklist

After updating imports:

- [ ] TypeScript compiles: `npx tsc --noEmit`
- [ ] No import errors in IDE
- [ ] Build succeeds: `npm run build`
- [ ] All barrel exports updated
- [ ] Tests still pass (if any)

---

## Import Update Template

```markdown
## Import Path Update Report

**Date**: [Date]
**Reason**: [File move / Rename / Reorganization]

### Changes Made

| Original Path | New Path |
|--------------|----------|
| `components/OldPath/A` | `components/NewPath/A` |
| `components/OldPath/B` | `components/NewPath/B` |

### Files Updated

| File | Line | Change |
|------|------|--------|
| `pages/Home.tsx` | 5 | Updated import path |
| `pages/Dashboard.tsx` | 12 | Updated import path |

### Barrel Exports Updated

| Index File | Change |
|------------|--------|
| `components/OldPath/index.ts` | Removed exports |
| `components/NewPath/index.ts` | Added exports |

### Verification

- [x] TypeScript check passed
- [x] Build succeeded
- [ ] Visual verification in browser
```

---

## Prevention Tips

1. **Use barrel exports** - Changing internal paths only requires updating index.ts
2. **Use path aliases** - `@/components/...` is easier to update than relative paths
3. **Plan structure early** - Minimize moves by having good initial organization
4. **Update incrementally** - Move one component at a time, verify, repeat
