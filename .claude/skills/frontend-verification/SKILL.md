---
name: frontend-verification
description: Comprehensive frontend verification workflow using Playwright MCP tools. Use after creating or modifying React components to verify rendering, check console errors, test responsive breakpoints, and run the test suite. Closes the loop on component development.
---

# Frontend Verification Skill

## Overview

This skill provides a complete verification workflow for React components using Playwright MCP tools. It verifies that components render correctly, have no console errors, work at different breakpoints, and pass tests.

---

## CRITICAL: Browser Tab Management

**IMPORTANT**: When multiple agents run Playwright verification in parallel, they MUST use separate browser tabs to avoid conflicts.

### Before Starting Verification:
1. Check existing tabs: `mcp__playwright__browser_tabs` with action: "list"
2. Create a NEW tab: `mcp__playwright__browser_tabs` with action: "new"
3. Note the tab index returned
4. Use that tab for all your operations

### After Verification:
1. Close your tab: `mcp__playwright__browser_tabs` with action: "close", index: [your tab index]

### Example Workflow:
```
1. browser_tabs action: "list"          # See existing tabs
2. browser_tabs action: "new"           # Create new tab, returns index
3. browser_tabs action: "select" index: N  # Select your new tab
4. browser_navigate url: "..."          # Navigate in YOUR tab
5. browser_snapshot                      # Verify in YOUR tab
6. browser_tabs action: "close" index: N # Clean up YOUR tab
```

---

## When to Use

- After creating a new React component
- After modifying existing components
- Before committing code
- When visual issues are reported
- To verify responsive design

---

## Verification Workflow

### Step 1: Start Development Server

```bash
# Start the dev server in background
cd frontend && npm run dev
```

Wait for the server to be ready (usually shows "Local: http://localhost:5173").

**NOTE**: Only ONE agent should start the dev server. Others should check if it's already running first.

### Step 2: Navigate to the Page

Use Playwright to open the page containing your component:

```
mcp__playwright__browser_navigate
url: "http://localhost:5173/path-to-page"
```

### Step 3: Take Accessibility Snapshot

Get a structured view of what's rendered:

```
mcp__playwright__browser_snapshot
```

This returns the accessibility tree showing all rendered elements, text, and interactive components.

### Step 4: Check Console for Errors

```
mcp__playwright__browser_console_messages
level: "error"
```

Look for:
- React errors (hooks, state, props)
- TypeScript runtime errors
- Failed API calls
- Missing imports
- Context provider errors

### Step 5: Take Visual Screenshot

```
mcp__playwright__browser_take_screenshot
type: "png"
filename: "component-verification.png"
```

Then read the screenshot to visually verify:
- Layout is correct
- Colors match design tokens
- Text is readable
- Images load properly

### Step 6: Test Responsive Breakpoints

Test each breakpoint:

```
# Mobile (375px)
mcp__playwright__browser_resize
width: 375
height: 667

mcp__playwright__browser_take_screenshot
filename: "mobile-375.png"

# Tablet (768px)
mcp__playwright__browser_resize
width: 768
height: 1024

mcp__playwright__browser_take_screenshot
filename: "tablet-768.png"

# Desktop (1280px)
mcp__playwright__browser_resize
width: 1280
height: 800

mcp__playwright__browser_take_screenshot
filename: "desktop-1280.png"
```

### Step 7: Run Test Suite

```bash
# Run all frontend tests
cd frontend && npm test

# Run specific component tests
cd frontend && npm test -- --grep "ComponentName"

# Run E2E tests (requires dev server running)
cd frontend && npx playwright test

# Run specific E2E test file
cd frontend && npx playwright test e2e/tests/feature/feature.spec.ts
```

---

## Quick Verification Checklist

After component creation, verify:

- [ ] Page loads without errors (`browser_navigate` + `browser_console_messages`)
- [ ] Component renders (`browser_snapshot`)
- [ ] No console errors at error/warning level
- [ ] Visual appearance correct (`browser_take_screenshot`)
- [ ] Mobile layout works (375px resize + screenshot)
- [ ] Tablet layout works (768px resize + screenshot)
- [ ] Desktop layout works (1280px resize + screenshot)
- [ ] Unit tests pass (`npm test`)
- [ ] E2E tests pass (`npx playwright test`)

---

## Common Issues and Fixes

### Issue: "Cannot read property of undefined"
**Cause**: Missing context provider or props
**Check**: `browser_console_messages` level: "error"
**Fix**: Wrap component in required provider

### Issue: White screen / nothing renders
**Cause**: JavaScript error preventing render
**Check**: Console errors, verify imports
**Fix**: Check for syntax errors, missing exports

### Issue: Layout broken on mobile
**Cause**: Missing responsive classes
**Check**: Resize to 375px and screenshot
**Fix**: Add `md:`, `lg:` Tailwind breakpoint prefixes

### Issue: Wrong colors
**Cause**: Hardcoded colors instead of tokens
**Check**: Visual screenshot comparison
**Fix**: Use `tactical-*` and `tiger-orange` tokens

### Issue: Tests timeout
**Cause**: Dev server not running
**Check**: Is `npm run dev` running?
**Fix**: Start dev server before running E2E tests

---

## Tiger ID Specific Routes

| Page | Route | What to Verify |
|------|-------|----------------|
| Dashboard | `/dashboard` | Charts render, stats load |
| Investigation | `/investigation2` | Upload zone, progress, results |
| Tigers | `/tigers` | Grid, filters, cards |
| Facilities | `/facilities` | Map, list, filters |
| Verification | `/verification` | Queue table, comparison overlay |
| Discovery | `/discovery` | Crawl grid, activity feed |

---

## Playwright MCP Tools Reference

| Tool | Purpose |
|------|---------|
| `browser_navigate` | Open a URL |
| `browser_snapshot` | Get accessibility tree (better than screenshot for structure) |
| `browser_take_screenshot` | Visual capture |
| `browser_console_messages` | Get console logs/errors |
| `browser_resize` | Change viewport size |
| `browser_click` | Interact with elements |
| `browser_type` | Enter text in inputs |
| `browser_evaluate` | Run JavaScript on page |

---

## Full Verification Script

For comprehensive verification, run this sequence:

1. `cd frontend && npm run dev` (background)
2. `mcp__playwright__browser_navigate` to page
3. `mcp__playwright__browser_console_messages` level: "error"
4. `mcp__playwright__browser_snapshot`
5. `mcp__playwright__browser_take_screenshot`
6. `mcp__playwright__browser_resize` to 375px → screenshot
7. `mcp__playwright__browser_resize` to 768px → screenshot
8. `mcp__playwright__browser_resize` to 1280px → screenshot
9. `cd frontend && npm test`
10. `cd frontend && npx playwright test`

This provides complete verification that the component works correctly.
