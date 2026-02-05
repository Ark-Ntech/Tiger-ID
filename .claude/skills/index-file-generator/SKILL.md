---
name: index-file-generator
description: Automatically creates and updates barrel export files (index.ts) for React component directories. Use after creating new components to ensure they are properly exported and discoverable. Maintains clean import paths across the codebase.
---

# Index File Generator Skill

## Overview

This skill creates and maintains barrel export files (index.ts) for component directories. Barrel exports provide clean import paths and ensure all components are properly discoverable.

---

## When to Use

- After creating a new component in a directory
- After creating a new component directory
- When imports are failing due to missing exports
- When user asks to "update exports" or "fix imports"
- During codebase cleanup/organization

---

## Process

### Step 1: Identify Directory Structure

Scan the component directory to find all exportable files:

```
frontend/src/components/
├── common/
│   ├── Button.tsx
│   ├── Card.tsx
│   ├── Input.tsx
│   ├── EmptyState.tsx
│   └── index.ts          # Barrel export
├── investigations/
│   ├── progress/
│   │   ├── ModelProgressGrid.tsx
│   │   ├── LiveActivityFeed.tsx
│   │   └── index.ts      # Sub-directory barrel
│   ├── results/
│   │   └── tabs/
│   │       ├── OverviewTab.tsx
│   │       └── index.ts
│   └── index.ts          # Parent barrel
```

### Step 2: Generate Barrel Export

Create index.ts with named exports:

```typescript
// frontend/src/components/common/index.ts
export { default as Button } from './Button'
export { default as Card } from './Card'
export { default as Input } from './Input'
export { default as EmptyState } from './EmptyState'
export { default as ErrorState } from './ErrorState'
export { default as LoadingSpinner } from './LoadingSpinner'
export { default as Badge } from './Badge'
export { default as Skeleton } from './Skeleton'
export { default as Toast } from './Toast'

// Also export any types
export type { ButtonProps } from './Button'
export type { CardProps } from './Card'
```

### Step 3: Handle Sub-directories

Re-export from sub-directories:

```typescript
// frontend/src/components/investigations/index.ts
// Direct exports
export { default as Investigation2Upload } from './Investigation2Upload'
export { default as Investigation2Progress } from './Investigation2Progress'
export { default as Investigation2ResultsEnhanced } from './Investigation2ResultsEnhanced'

// Re-export from sub-directories
export * from './progress'
export * from './results'
export * from './tabs'
```

### Step 4: Update Parent Exports

Ensure parent directories also export new components:

```typescript
// frontend/src/components/index.ts
export * from './common'
export * from './investigations'
export * from './layout'
export * from './tigers'
export * from './discovery'
export * from './dashboard'
export * from './facilities'
export * from './verification'
```

---

## Export Patterns

### Default Export Pattern
```typescript
// Component file
const Button = () => { ... }
export default Button

// index.ts
export { default as Button } from './Button'
```

### Named Export Pattern
```typescript
// Component file
export const Button = () => { ... }

// index.ts
export { Button } from './Button'
```

### Type Export Pattern
```typescript
// index.ts
export type { ButtonProps } from './Button'
export type { Tiger, TigerMatch } from '../types'
```

### Mixed Pattern (Component + Types)
```typescript
// index.ts
export { default as TigerCard } from './TigerCard'
export type { TigerCardProps } from './TigerCard'
```

---

## Tiger ID Directory Structure

### Standard Directories
```
frontend/src/components/
├── common/index.ts           # Button, Card, Input, EmptyState, ErrorState
├── layout/index.ts           # Header, Sidebar, Layout, MobileNav
├── investigations/
│   ├── progress/index.ts     # ModelProgressGrid, LiveActivityFeed
│   ├── results/index.ts      # MatchCard, MatchFilters
│   ├── tabs/index.ts         # OverviewTab, DetectionTab, etc.
│   └── index.ts              # Investigation2Upload, Investigation2Progress
├── tigers/index.ts           # TigerCard, TigerFilters, TigerUploadWizard
├── discovery/index.ts        # FacilityCrawlGrid, DiscoveryActivityFeed
├── dashboard/index.ts        # SubagentActivityPanel, QuickStatsGrid
├── facilities/index.ts       # FacilityMapView, FacilityFilters
└── verification/index.ts     # VerificationComparisonOverlay, BulkVerificationActions
```

---

## Automation Script

For bulk generation, use this pattern:

```bash
# Find all component directories
find frontend/src/components -type d

# For each directory, list .tsx files (excluding index.tsx)
ls frontend/src/components/common/*.tsx | grep -v index
```

### Generate index.ts content:
```bash
cd frontend/src/components/common
for file in *.tsx; do
  if [[ "$file" != "index.tsx" ]]; then
    name="${file%.tsx}"
    echo "export { default as $name } from './$name'"
  fi
done
```

---

## Verification

After generating index files:

1. **Type check**: `cd frontend && npx tsc --noEmit`
2. **Build check**: `cd frontend && npm run build`
3. **Import test**: Try importing from barrel in another file

```typescript
// Should work after index.ts is correct
import { Button, Card, EmptyState } from '../components/common'
import { TigerCard, TigerFilters } from '../components/tigers'
```

---

## Common Issues

### Issue 1: Circular Dependency
**Symptom**: Import resolution fails
**Fix**: Move shared types to separate `types/` directory

### Issue 2: Default vs Named Export Mismatch
**Symptom**: `Module has no default export`
**Fix**: Match export style in index.ts to component file

### Issue 3: Missing Type Export
**Symptom**: Type not found when importing
**Fix**: Add explicit type export: `export type { Props } from './Component'`

---

## Index File Template

```typescript
/**
 * Barrel exports for [directory] components
 *
 * Usage:
 * import { ComponentA, ComponentB } from '@/components/[directory]'
 */

// Components
export { default as ComponentA } from './ComponentA'
export { default as ComponentB } from './ComponentB'

// Types (if any)
export type { ComponentAProps } from './ComponentA'

// Re-exports from sub-directories (if any)
export * from './subdirectory'
```
