---
name: design-token-auditor
description: Scans React components for hardcoded colors, spacing, and other values that should use design tokens. Use this skill to maintain design consistency and catch styling issues. Identifies violations of the Tiger ID design system.
---

# Design Token Auditor Skill

## Overview

This skill audits React components for hardcoded design values that should use design tokens from Tailwind configuration. It helps maintain visual consistency across the Tiger ID application.

---

## When to Use

- After creating new components
- During code review
- When user asks to "audit styling" or "check design tokens"
- When visual inconsistencies are noticed
- Before major releases

---

## Tiger ID Design System

### Color Tokens (Tailwind)

```javascript
// tailwind.config.js
colors: {
  // Primary brand colors
  'tiger-orange': {
    DEFAULT: '#ff6b35',
    light: '#ff8c5a',
    dark: '#e55a2b'
  },

  // Tactical (slate-based neutrals)
  'tactical': {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
    950: '#020617'
  }
}
```

### Violations to Find

| Hardcoded | Should Be |
|-----------|-----------|
| `bg-gray-900` | `bg-tactical-900` |
| `bg-gray-800` | `bg-tactical-800` |
| `text-gray-400` | `text-tactical-400` |
| `border-gray-700` | `border-tactical-700` |
| `#ff6b35` | `tiger-orange` |
| `#1e293b` | `tactical-800` |
| `bg-orange-500` | `bg-tiger-orange` |
| `text-blue-500` | `text-tiger-orange` (if primary action) |

---

## Audit Process

### Step 1: Scan for Hardcoded Colors

Search for common violations:

```bash
# Find gray colors (should be tactical)
grep -r "gray-[0-9]" frontend/src/components/

# Find hardcoded hex colors
grep -rE "#[0-9a-fA-F]{3,6}" frontend/src/components/

# Find orange that's not tiger-orange
grep -r "orange-[0-9]" frontend/src/components/
```

### Step 2: Generate Audit Report

For each file, check:

1. **Background colors**: `bg-*`
2. **Text colors**: `text-*`
3. **Border colors**: `border-*`
4. **Ring/outline colors**: `ring-*`, `outline-*`
5. **Shadow colors**: `shadow-*`
6. **Inline styles**: `style={{ color: ... }}`

### Step 3: Categorize Violations

| Severity | Description | Example |
|----------|-------------|---------|
| Critical | Primary brand color wrong | `bg-orange-500` instead of `bg-tiger-orange` |
| High | Neutral color inconsistent | `bg-gray-900` instead of `bg-tactical-900` |
| Medium | Non-standard spacing | `p-7` instead of `p-6` or `p-8` |
| Low | Slight variation | `bg-tactical-850` (non-existent) |

### Step 4: Fix Violations

Apply token replacements:

```typescript
// Before
<div className="bg-gray-900 text-gray-100 border-gray-700">

// After
<div className="bg-tactical-900 text-tactical-100 border-tactical-700">
```

---

## Component-Specific Rules

### Sidebar
```typescript
// Correct tokens
bg-tactical-950        // Main background
border-tactical-800    // Dividers
text-tactical-300      // Inactive nav items
text-tactical-400      // Secondary text
bg-tiger-orange        // Active nav item
```

### Buttons
```typescript
// Primary
bg-tiger-orange hover:bg-tiger-orange-dark

// Secondary
bg-tactical-200 dark:bg-tactical-700

// Ghost
text-tactical-700 hover:bg-tactical-100 dark:text-tactical-300 dark:hover:bg-tactical-800

// Danger
bg-red-600 hover:bg-red-700 (keep red for semantic meaning)
```

### Cards
```typescript
// Light mode
bg-white border-tactical-200

// Dark mode
dark:bg-tactical-800 dark:border-tactical-700
```

### Forms
```typescript
// Inputs
bg-white border-tactical-300 focus:ring-tiger-orange
dark:bg-tactical-800 dark:border-tactical-600

// Labels
text-tactical-700 dark:text-tactical-300
```

---

## Audit Report Template

```markdown
# Design Token Audit Report

**Date**: [Date]
**Files Audited**: [Number]
**Violations Found**: [Number]

## Critical Violations

| File | Line | Issue | Fix |
|------|------|-------|-----|
| Sidebar.tsx | 34 | `bg-gray-900` | `bg-tactical-900` |

## High Priority

| File | Line | Issue | Fix |
|------|------|-------|-----|
| Button.tsx | 15 | `primary-600` (undefined) | `tiger-orange` |

## Recommendations

1. Update Sidebar.tsx lines 34, 39, 52
2. Fix Button.tsx undefined color reference
3. Add missing dark mode variants to Card.tsx
```

---

## Automated Checks

### Grep Patterns

```bash
# All gray colors (should be tactical)
grep -rn "\\b(bg|text|border|ring)-gray-" frontend/src/

# Hardcoded orange (should be tiger-orange)
grep -rn "\\b(bg|text|border)-orange-" frontend/src/

# Undefined tokens
grep -rn "primary-[0-9]" frontend/src/

# Inline color styles
grep -rn "style=.*color:" frontend/src/
```

### ESLint Rule (Future)

```javascript
// Could add custom ESLint rule
{
  "rules": {
    "tiger-id/no-hardcoded-colors": "error"
  }
}
```

---

## Exceptions

Some hardcoded colors are acceptable:

| Color | Acceptable Use |
|-------|---------------|
| `red-*` | Error states, danger buttons |
| `green-*` | Success states, confirmations |
| `yellow-*` | Warning states |
| `blue-*` | Info states, links (if not primary) |

These semantic colors should NOT be replaced with tiger-orange.

---

## Integration

After auditing:

1. Create a fix list prioritized by severity
2. Fix critical violations first
3. Run TypeScript check after fixes
4. Visual review in browser
5. Update this audit as new patterns emerge
