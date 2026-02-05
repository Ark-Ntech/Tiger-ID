---
name: component-integration-tester
description: Verifies that newly created React components integrate correctly with their parent pages. Use after creating components to ensure they render without errors, have correct props, and work within the application context. Catches integration issues early.
---

# Component Integration Tester Skill

## Overview

This skill verifies that newly created React components integrate correctly with their parent pages and the application context. Use it after creating components to catch integration issues before they reach production.

---

## When to Use

- After creating a new component that will be used in a page
- After modifying component props or interfaces
- When a component needs to work with Context providers
- After refactoring component hierarchies
- When user asks to "test integration" or "verify component works"

---

## Process

### Step 1: Identify Integration Points

For a new component, identify:

1. **Parent page(s)** that will use it
2. **Props** it expects
3. **Context providers** it needs
4. **State management** (Redux, Context, local)
5. **API calls** it makes

### Step 2: Check Import Paths

Verify the component can be imported:

```typescript
// In the parent page, check:
import { NewComponent } from '../components/path/NewComponent'
// Or from barrel export:
import { NewComponent } from '../components/path'
```

### Step 3: Verify Props Interface

Ensure props match between component and usage:

```typescript
// Component defines:
interface NewComponentProps {
  data: Tiger[]
  onSelect: (id: string) => void
  isLoading?: boolean
}

// Parent passes:
<NewComponent
  data={tigers}           // ✓ Tiger[] matches
  onSelect={handleSelect} // ✓ Function signature matches
  isLoading={loading}     // ✓ Optional prop
/>
```

### Step 4: Check Context Requirements

If component uses context:

```typescript
// Component uses:
const { state, dispatch } = useInvestigation2Context()

// Parent must have provider:
<Investigation2Provider>
  <NewComponent />
</Investigation2Provider>
```

### Step 5: Verify API Integration

If component fetches data:

```typescript
// Check RTK Query hook exists:
import { useGetTigersQuery } from '../app/api'

// Verify API endpoint is defined in api.ts
```

---

## Integration Checklist

### Component Creation
- [ ] Component file created in correct location
- [ ] TypeScript types defined (props interface)
- [ ] Exported from component file
- [ ] Added to barrel export (index.ts) if applicable

### Parent Integration
- [ ] Import statement added to parent page
- [ ] Props passed correctly
- [ ] Event handlers connected
- [ ] Conditional rendering logic correct

### Context & State
- [ ] Context providers wrap component
- [ ] Redux selectors return expected data
- [ ] Local state initialized correctly

### API Integration
- [ ] RTK Query hooks available
- [ ] Loading states handled
- [ ] Error states handled
- [ ] Data transformation correct

---

## Common Integration Issues

### Issue 1: Missing Context Provider

**Symptom**: `Cannot read property 'state' of undefined`

**Fix**: Wrap component in required provider:
```tsx
<Investigation2Provider>
  <YourComponent />
</Investigation2Provider>
```

### Issue 2: Props Mismatch

**Symptom**: TypeScript error about missing/wrong props

**Fix**: Update either component props or parent usage to match

### Issue 3: Missing Export

**Symptom**: `Module has no exported member`

**Fix**: Add to barrel export:
```typescript
// components/path/index.ts
export { NewComponent } from './NewComponent'
```

### Issue 4: Circular Dependency

**Symptom**: Module evaluation fails

**Fix**: Move shared types to separate file, use lazy imports

---

## Tiger ID Specific Patterns

### Investigation Components
```typescript
// Must be inside Investigation2Provider
// Use useInvestigation2Context() for state
// Connect to WebSocket for real-time updates
```

### Tiger Components
```typescript
// Use useGetTigersQuery() from api.ts
// Handle pagination with offset/limit
// Support filter props interface
```

### Dashboard Components
```typescript
// Use multiple RTK Query hooks
// Handle loading states individually
// Support time range filtering
```

---

## Verification Commands

```bash
# TypeScript check
cd frontend && npx tsc --noEmit

# Build check (catches more issues)
cd frontend && npm run build

# Dev server check (runtime verification)
cd frontend && npm run dev
# Then manually navigate to page using component
```

---

## Integration Report Template

After testing, document:

```markdown
## Component: [ComponentName]

**Location**: `src/components/path/ComponentName.tsx`

**Parent Pages**:
- `src/pages/PageName.tsx` - Line 45

**Integration Status**: ✓ Verified / ✗ Issues Found

**Context Requirements**:
- Investigation2Provider: ✓
- Redux Store: ✓

**Props Verified**:
- data: Tiger[] ✓
- onSelect: (id) => void ✓
- isLoading: boolean ✓

**Issues Found**:
- None / [List issues]
```
