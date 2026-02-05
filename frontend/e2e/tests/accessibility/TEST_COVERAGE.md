# Accessibility Test Coverage

Complete breakdown of accessibility test coverage for Tiger ID.

## 📊 Summary Statistics

- **Total Test Suites**: 13
- **Total Test Cases**: 30
- **Individual Assertions**: ~90 (across 3 browsers)
- **Pages Covered**: 8
- **WCAG Standards**: 4 (2.0 A/AA, 2.1 A/AA)
- **Violation Impacts Tracked**: 4 (Critical, Serious, Moderate, Minor)

## 🎯 Test Suites Breakdown

### 1. Authentication Pages (2 tests)
Tests login and password reset pages for accessibility compliance.

| Test | What It Checks |
|------|----------------|
| Login page violations | WCAG 2.0/2.1 A/AA compliance on login page |
| Password reset violations | WCAG 2.0/2.1 A/AA compliance on password reset |

**WCAG Criteria Covered**: 1.1.1, 1.3.1, 1.4.3, 2.1.1, 2.4.1, 3.3.2, 4.1.2

---

### 2. Main Dashboard and Navigation (3 tests)
Tests dashboard page, navigation header, and sidebar accessibility.

| Test | What It Checks |
|------|----------------|
| Dashboard violations | Full dashboard page compliance |
| Navigation ARIA labels | Proper landmark regions and labels |
| Sidebar keyboard accessibility | Keyboard navigation in sidebar |

**WCAG Criteria Covered**: 2.1.1, 2.4.1, 2.4.3, 4.1.2

---

### 3. Tiger Management Pages (3 tests)
Tests tiger list, cards, and detail pages.

| Test | What It Checks |
|------|----------------|
| Tigers list violations | Full tigers list page compliance |
| Tiger cards alt text | Image alt text on all tiger cards |
| Tiger detail page violations | Full tiger detail page compliance |

**WCAG Criteria Covered**: 1.1.1, 1.3.1, 2.4.6, 4.1.2

---

### 4. Investigation Pages (3 tests)
Tests Investigation 2.0 upload and results pages.

| Test | What It Checks |
|------|----------------|
| Investigation page violations | Full investigation page compliance |
| File upload labels | Proper labels and instructions for file uploads |
| Investigation results structure | Proper heading hierarchy and structure |

**WCAG Criteria Covered**: 1.3.1, 2.4.6, 3.3.2, 4.1.2

---

### 5. Discovery Pages (2 tests)
Tests discovery pipeline page and controls.

| Test | What It Checks |
|------|----------------|
| Discovery page violations | Full discovery page compliance |
| Discovery controls keyboard | Keyboard accessibility of all controls |

**WCAG Criteria Covered**: 2.1.1, 4.1.2

---

### 6. Facilities Pages (3 tests)
Tests facilities list, map, and cards.

| Test | What It Checks |
|------|----------------|
| Facilities page violations | Full facilities page compliance |
| Facility map alternatives | Text alternatives for Leaflet map |
| Facility cards structure | Semantic HTML structure for cards |

**WCAG Criteria Covered**: 1.1.1, 1.3.1, 2.4.1, 4.1.2

---

### 7. Verification Queue (2 tests)
Tests verification queue and action buttons.

| Test | What It Checks |
|------|----------------|
| Verification page violations | Full verification page compliance |
| Action button labels | Clear accessible names for all buttons |

**WCAG Criteria Covered**: 4.1.2, 2.4.6

---

### 8. Modal Components (2 tests)
Tests modal dialogs for focus trapping and accessibility.

| Test | What It Checks |
|------|----------------|
| Modal focus trapping | Proper aria-modal, aria-labelledby |
| Modal close buttons | Focusable close buttons with accessible names |

**WCAG Criteria Covered**: 2.1.1, 2.4.3, 4.1.2

---

### 9. Form Components (3 tests)
Tests form inputs, validation errors, and required fields.

| Test | What It Checks |
|------|----------------|
| Form input labels | All inputs have associated labels |
| Validation error announcements | Errors use role="alert" or aria-live |
| Required field indicators | Required fields have aria-required |

**WCAG Criteria Covered**: 1.3.1, 3.3.1, 3.3.2, 4.1.2

---

### 10. Color Contrast (1 test)
Tests color contrast across all pages.

| Test | What It Checks |
|------|----------------|
| All pages contrast requirements | 4.5:1 minimum contrast ratio (WCAG AA) |

**Pages Tested**: Login, Dashboard, Tigers, Facilities, Investigation, Discovery, Verification

**WCAG Criteria Covered**: 1.4.3

---

### 11. Keyboard Navigation (3 tests)
Tests keyboard accessibility and navigation.

| Test | What It Checks |
|------|----------------|
| Interactive elements keyboard accessible | All clickable elements are focusable |
| Skip to main content link | Skip link present and functional |
| Tab order logical | Natural tab order without positive tabindex |

**WCAG Criteria Covered**: 2.1.1, 2.4.1

---

### 12. Screen Reader Compatibility (2 tests)
Tests document structure and live regions.

| Test | What It Checks |
|------|----------------|
| Document structure | Main landmark, proper heading hierarchy |
| Live regions marked | Dynamic content uses aria-live |

**WCAG Criteria Covered**: 1.3.1, 2.4.1, 4.1.3

---

### 13. Comprehensive Scan Summary (1 test)
Generates full report across all critical pages.

| Test | What It Checks |
|------|----------------|
| Generate accessibility report | Scans all 7 major pages, reports violations by impact |

**Output**: Summary table with violation counts by page and impact level

---

## 🔍 WCAG Success Criteria Coverage

### Level A (Must Have)
- ✅ 1.1.1 Non-text Content (images have alt text)
- ✅ 1.3.1 Info and Relationships (semantic HTML)
- ✅ 2.1.1 Keyboard (all functionality keyboard accessible)
- ✅ 2.4.1 Bypass Blocks (skip links, landmarks)
- ✅ 3.3.1 Error Identification (errors clearly identified)
- ✅ 3.3.2 Labels or Instructions (form labels present)
- ✅ 4.1.2 Name, Role, Value (proper ARIA)

### Level AA (Should Have)
- ✅ 1.4.3 Contrast (Minimum) (4.5:1 ratio)
- ✅ 2.4.3 Focus Order (logical focus sequence)
- ✅ 2.4.6 Headings and Labels (descriptive headings)
- ✅ 4.1.3 Status Messages (live regions for status)

### Level AAA (Nice to Have)
- ⚠️ Not explicitly tested (but may pass)

---

## 📈 Test Execution Matrix

| Browser | Tests | Setup | Total Runs |
|---------|-------|-------|------------|
| Chromium | 30 | 1 | 31 |
| Firefox | 30 | 1 | 31 |
| WebKit | 30 | 1 | 31 |
| **Total** | **90** | **3** | **93** |

Each test runs in all 3 browsers automatically via Playwright.

---

## 🎨 Violation Impact Levels

Tests check for violations at 4 impact levels:

| Impact | Severity | Test Behavior |
|--------|----------|---------------|
| **Critical** | Blocks users completely | ❌ **Test fails** |
| **Serious** | Creates significant barriers | ❌ **Test fails** |
| **Moderate** | Causes inconvenience | ⚠️ Logged only |
| **Minor** | Causes annoyance | ⚠️ Logged only |

**Philosophy**: Critical and serious violations must be fixed before merging. Moderate and minor violations are tracked but don't block development.

---

## 🔄 Continuous Monitoring

### What Gets Tested
Every test run checks:
- All 8 major pages
- All modal dialogs
- All form interactions
- All images
- All buttons
- Color contrast
- Keyboard navigation
- Screen reader compatibility

### When Tests Run
- **Locally**: On demand via `npm run test:e2e:accessibility`
- **CI/CD**: On every pull request (recommended)
- **Scheduled**: Nightly full scan (recommended)

---

## 📋 Test Scenarios by User Impact

### High Priority (Blocking Issues)
These tests catch violations that prevent users from accessing content:

1. Image alt text (blind users can't understand images)
2. Form labels (screen readers can't identify fields)
3. Keyboard navigation (motor impairment users rely on keyboard)
4. Modal focus trapping (keyboard users get stuck)
5. Color contrast (low vision users can't read text)

### Medium Priority (Significant Barriers)
These tests catch violations that make content difficult to access:

1. Heading hierarchy (screen reader users navigate by headings)
2. Button names (unclear purpose for screen reader users)
3. ARIA labels (assistive tech needs proper semantics)
4. Live regions (dynamic updates not announced)

### Lower Priority (Usability Issues)
These tests catch violations that cause minor inconvenience:

1. Skip links (nice to have for keyboard efficiency)
2. Table structure (helps with navigation)
3. List semantics (helps with understanding)

---

## 🛠️ Tools and Technologies

- **@axe-core/playwright**: Automated accessibility testing engine
- **axe-core rules**: 90+ WCAG compliance rules
- **Playwright**: Cross-browser test execution
- **WCAG 2.0/2.1**: Accessibility standards
- **ARIA**: Accessible Rich Internet Applications spec

---

## 📊 Expected Baseline

### Ideal State (Target)
```
=== ACCESSIBILITY SCAN SUMMARY ===
Pages tested: 7
Pages with violations: 0
Total violations: 0
  Critical: 0
  Serious: 0
  Moderate: 0
  Minor: 0
==================================
```

### Acceptable State (Current Goal)
```
=== ACCESSIBILITY SCAN SUMMARY ===
Pages tested: 7
Pages with violations: 2
Total violations: 8
  Critical: 0
  Serious: 0
  Moderate: 5
  Minor: 3
==================================
```

### Unacceptable State (Blocks Merge)
```
=== ACCESSIBILITY SCAN SUMMARY ===
Pages tested: 7
Pages with violations: 4
Total violations: 15
  Critical: 2    ← BLOCKING
  Serious: 3     ← BLOCKING
  Moderate: 7
  Minor: 3
==================================
```

---

## 🔗 Related Documentation

- [README.md](./README.md) - Full test documentation
- [QUICK_START.md](./QUICK_START.md) - Get started in 5 minutes
- [../../../docs/TESTING.md](../../../docs/TESTING.md) - Overall testing strategy

---

## 📝 Coverage Gaps and Future Work

### Not Yet Covered
- [ ] PDF export accessibility
- [ ] Chart/graph screen reader compatibility
- [ ] Animation/motion preferences (prefers-reduced-motion)
- [ ] Print styles
- [ ] High contrast mode
- [ ] Zoom/text scaling (up to 200%)
- [ ] Touch target sizes (mobile)

### Planned Additions
- [ ] Add tests for new Discovery components
- [ ] Add tests for notification system
- [ ] Add tests for settings/preferences page
- [ ] Add tests for help/documentation pages
- [ ] Add mobile viewport accessibility tests

---

## 🎯 Success Metrics

### Test Health
- ✅ All critical/serious violations: **0**
- 🎯 Test execution time: **< 5 minutes**
- 🎯 Test success rate: **> 95%**
- 🎯 Coverage: **All major user flows**

### Product Health
- 🎯 Keyboard navigation score: **100%**
- 🎯 Screen reader compatibility: **100%**
- 🎯 Color contrast: **WCAG AA compliant**
- 🎯 axe-core score: **0 critical/serious violations**

---

## 📞 Support

Questions or issues with accessibility tests?

1. Check [QUICK_START.md](./QUICK_START.md) for common issues
2. Review [README.md](./README.md) for detailed documentation
3. Check axe-core help URLs in test output
4. Consult [WCAG Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
