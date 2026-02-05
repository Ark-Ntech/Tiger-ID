# Visual Regression Testing - File Index

Complete overview of all visual regression testing files and documentation.

## Created: 2026-02-05

## Test Files

### `visual.spec.ts`
**Main visual regression test suite** with 87+ comprehensive tests covering:
- 15 test suites organized by feature
- Light/dark mode variations for all major pages
- Responsive layouts (desktop/tablet/mobile)
- Component states (empty, error, loading, hover)
- Interactive elements (modals, toasts, badges, cards)

**Lines:** ~1,700
**Test Count:** 87+ tests
**Coverage:** All major pages and components

### `helpers.test.ts`
**Unit tests for visual helper functions** ensuring utilities work correctly:
- `toggleDarkMode()` tests
- `waitForPageLoad()` tests
- `waitForImages()` tests
- `hideTimestamps()` tests
- `maskDynamicIds()` tests
- Integration and edge case tests

**Lines:** ~600
**Test Count:** 35+ helper tests
**Coverage:** All helper functions

## Documentation Files

### `README.md` (Full Documentation)
**Comprehensive guide** covering everything about visual regression testing:
- Complete test coverage breakdown
- Running tests (all modes)
- Screenshot configuration
- Helper function reference
- Best practices (8 key practices)
- Troubleshooting (8 common issues)
- CI/CD integration examples
- Maintenance guidelines

**Lines:** ~650
**Sections:** 15 major sections

### `QUICK_REFERENCE.md` (Command Cheat Sheet)
**Fast command reference** for daily use:
- Common commands table
- Test organization by feature/component/theme/viewport
- Typical workflow examples (5 workflows)
- Helper function quick reference
- Troubleshooting quick fixes
- NPM script definitions

**Lines:** ~400
**Sections:** 11 reference sections

### `RUN_TESTS.md` (Step-by-Step Guide)
**Practical guide** for running tests:
- Prerequisites and first-time setup
- 6 common workflows with step-by-step instructions
- Test organization examples
- Understanding test results
- Detailed troubleshooting
- Environment setup requirements
- Performance optimization tips
- CI/CD integration

**Lines:** ~500
**Sections:** 10 practical guides

### `INDEX.md` (This File)
**Overview document** listing all files and their purposes.

## Quick Navigation

| Need to... | Use this file |
|-----------|---------------|
| **Run tests for the first time** | [RUN_TESTS.md](./RUN_TESTS.md) |
| **Find a specific command** | [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) |
| **Understand test coverage** | [README.md](./README.md) |
| **Debug failing tests** | [README.md](./README.md#troubleshooting) |
| **Add new visual tests** | [README.md](./README.md#adding-new-visual-tests) |
| **Update baselines** | [RUN_TESTS.md](./RUN_TESTS.md#workflow-2-updating-baselines-after-ui-changes) |
| **Review best practices** | [README.md](./README.md#best-practices) |
| **Check helper functions** | [README.md](./README.md#helper-functions) |
| **See test organization** | [RUN_TESTS.md](./RUN_TESTS.md#test-organization) |
| **CI/CD integration** | [README.md](./README.md#cicd-integration) |

## Test Coverage Summary

### Pages Tested (14 pages)
1. Login page (light/dark/mobile/validation)
2. Password reset page (light/dark)
3. Dashboard (light/dark/tablet/mobile/sections)
4. Tigers list (light/dark/mobile/cards/empty)
5. Tiger detail page
6. Investigation 2.0 (upload/progress/results/mobile)
7. Discovery pipeline (light/dark/mobile/grid/map)
8. Facilities list (light/dark/mobile/map/cards)
9. Facility detail page
10. Verification queue (light/dark/mobile/comparison)
11. Templates list (light/dark)
12. Empty states (variations)
13. Error states (variations)
14. Modals (variations)

### Components Tested (10+ components)
- Sidebar navigation
- Quick stats cards
- Analytics charts
- Tiger cards with badges
- Facility cards
- Investigation match cards
- Ensemble visualizations
- Progress indicators
- Filter bars
- Pagination controls
- Loading spinners
- Skeleton loaders
- Toast notifications
- Alert banners
- Confirmation dialogs

### Viewport Coverage
- **Desktop:** 1920×1080 (primary)
- **Tablet:** 768×1024 (iPad)
- **Mobile:** 375×667 (iPhone)

### Theme Coverage
- **Light mode:** All pages and components
- **Dark mode:** All pages and components

### Total Snapshots: 87+

## Helper Functions (5 utilities)

### `toggleDarkMode(page, enable)`
Enable or disable dark mode by adding/removing `dark` class.

### `waitForPageLoad(page)`
Wait for network idle and animations to complete.

### `waitForImages(page)`
Wait for all images to finish loading.

### `hideTimestamps(page)`
Hide dynamic timestamp elements to prevent false failures.

### `maskDynamicIds(page)`
Replace UUIDs with placeholders to prevent false failures.

## NPM Scripts

```json
{
  "test:e2e:visual": "playwright test tests/visual",
  "test:e2e:visual:update": "playwright test tests/visual --update-snapshots",
  "test:e2e:visual:ui": "playwright test tests/visual --ui",
  "test:e2e:visual:headed": "playwright test tests/visual --headed"
}
```

## Directory Structure

```
e2e/tests/visual/
├── visual.spec.ts              # Main test suite (87+ tests)
├── helpers.test.ts             # Helper function unit tests (35+ tests)
├── README.md                   # Full documentation (~650 lines)
├── QUICK_REFERENCE.md          # Command cheat sheet (~400 lines)
├── RUN_TESTS.md                # Step-by-step guide (~500 lines)
├── INDEX.md                    # This file
└── __snapshots__/              # Baseline screenshots (auto-generated)
    ├── login-light-desktop.png
    ├── dashboard-dark.png
    ├── tigers-list-light.png
    └── ... (87+ snapshot files)
```

## File Statistics

| File | Lines | Tests | Purpose |
|------|-------|-------|---------|
| `visual.spec.ts` | ~1,700 | 87+ | Main visual regression tests |
| `helpers.test.ts` | ~600 | 35+ | Helper function unit tests |
| `README.md` | ~650 | - | Full documentation |
| `QUICK_REFERENCE.md` | ~400 | - | Command reference |
| `RUN_TESTS.md` | ~500 | - | Step-by-step guide |
| `INDEX.md` | ~200 | - | This overview |
| **Total** | **~4,050** | **122+** | Complete visual testing suite |

## Getting Started

### 1. First Time Setup
```bash
cd frontend
npm install
npx playwright install --with-deps
```

### 2. Generate Baselines
```bash
# Start backend and frontend first
npm run test:e2e:visual:update
```

### 3. Run Tests
```bash
npm run test:e2e:visual
```

### 4. View Results
```bash
npm run test:e2e:report
```

## Common Commands

```bash
# Run all tests
npm run test:e2e:visual

# Update baselines
npm run test:e2e:visual:update

# Interactive UI
npm run test:e2e:visual:ui

# Run specific suite
npm run test:e2e:visual -- -g "Dashboard"

# Debug mode
npx playwright test tests/visual --debug
```

## Key Features

### Comprehensive Coverage
- ✅ 87+ visual snapshots
- ✅ 15 organized test suites
- ✅ All major pages and components
- ✅ Light and dark mode variations
- ✅ Responsive layout testing
- ✅ Component state variations

### Helper Utilities
- ✅ Dark mode toggle
- ✅ Page load waiting
- ✅ Image load waiting
- ✅ Timestamp hiding
- ✅ Dynamic ID masking

### Documentation
- ✅ Full comprehensive guide
- ✅ Quick reference sheet
- ✅ Step-by-step tutorials
- ✅ Troubleshooting guides
- ✅ Best practices
- ✅ CI/CD examples

### Testing Features
- ✅ Screenshot comparison
- ✅ Pixel-perfect diffing
- ✅ Configurable thresholds
- ✅ Multi-browser support
- ✅ Parallel execution
- ✅ HTML reports with diffs

## Integration

### Works With
- ✅ Playwright Test Runner
- ✅ GitHub Actions
- ✅ TailwindCSS dark mode
- ✅ React 18
- ✅ TypeScript
- ✅ Vite

### CI/CD Ready
- ✅ Automatic baseline comparison
- ✅ Artifact upload on failure
- ✅ HTML report generation
- ✅ Screenshot diff images
- ✅ Sharding support for parallel execution

## Maintenance

### When to Update Baselines
- ✅ Intentional UI changes
- ✅ Component styling updates
- ✅ Library upgrades
- ✅ Font or spacing changes

### Regular Tasks
- **Weekly:** Review failed tests
- **Before releases:** Full suite on all browsers
- **After updates:** Regenerate baselines
- **New features:** Add corresponding visual tests

## Support Resources

- [Full Documentation](./README.md) - Complete guide
- [Quick Reference](./QUICK_REFERENCE.md) - Command cheat sheet
- [Run Tests Guide](./RUN_TESTS.md) - Step-by-step instructions
- [Main E2E README](../README.md) - E2E testing overview
- [Playwright Docs](https://playwright.dev/docs/test-snapshots) - Official documentation

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-05 | 1.0.0 | Initial comprehensive visual regression suite created |

## Author Notes

This visual regression testing suite was designed to:
1. **Catch visual regressions early** before they reach production
2. **Document UI state** through comprehensive screenshots
3. **Support rapid development** with fast feedback loops
4. **Enable confident refactoring** with safety net of visual tests
5. **Maintain design consistency** across light/dark modes and viewports

All tests follow Playwright best practices and are optimized for:
- **Reliability:** Dynamic content masking, proper waits
- **Speed:** Parallel execution, smart timeouts
- **Maintainability:** Helper functions, clear organization
- **Debuggability:** UI mode, traces, detailed reports

---

**Quick Start:**
```bash
npm run test:e2e:visual:update  # Generate baselines
npm run test:e2e:visual         # Run tests
npm run test:e2e:report         # View results
```

For detailed instructions, see [RUN_TESTS.md](./RUN_TESTS.md)
