# Accessibility Test Scenarios

Complete list of accessibility test scenarios in the Tiger ID application.

## Test Organization

Tests are organized by functionality area and component type, with each test checking for WCAG 2.0/2.1 Level A and AA compliance.

## Test Scenarios by Category

### 1. Authentication Pages (2 tests)

#### Login Page
- **Test**: `Login page should not have accessibility violations`
- **Checks**:
  - Form labels present and properly associated
  - Color contrast meets WCAG AA standards
  - Keyboard navigation works
  - Focus indicators visible
  - Error messages are announced
  - Page structure (headings, landmarks)

#### Password Reset Page
- **Test**: `Password reset page should not have accessibility violations`
- **Checks**: Same as login page
- **URL**: `/password-reset`

---

### 2. Main Dashboard and Navigation (3 tests)

#### Dashboard Page
- **Test**: `Dashboard page should not have accessibility violations`
- **Checks**:
  - Proper heading hierarchy (h1 → h2 → h3)
  - Landmarks (main, nav, aside) present
  - Interactive elements keyboard accessible
  - Color contrast compliant
  - Statistics and charts have text alternatives
- **URL**: `/dashboard`

#### Navigation Header
- **Test**: `Navigation header should have proper ARIA labels`
- **Checks**:
  - `<nav>` element present
  - ARIA labels on navigation items
  - Active page indicated
  - Mobile menu accessible
- **Element**: `nav`

#### Sidebar Navigation
- **Test**: `Sidebar navigation should be keyboard accessible`
- **Checks**:
  - All links focusable with keyboard
  - Focus order is logical
  - Visual focus indicators
  - Semantic HTML structure
- **Element**: `aside, nav`

---

### 3. Tiger Management Pages (3 tests)

#### Tigers List Page
- **Test**: `Tigers list page should not have accessibility violations`
- **Checks**:
  - Grid/list semantic structure
  - Search input properly labeled
  - Filter controls accessible
  - Pagination controls keyboard accessible
  - Empty state has proper messaging
- **URL**: `/tigers`

#### Tiger Card Images
- **Test**: `Tiger cards should have proper alt text for images`
- **Checks**:
  - All `<img>` elements have `alt` attribute
  - Alt text is descriptive (not just "tiger image")
  - Decorative images use empty alt (`alt=""`)
  - Icons have ARIA labels
- **Element**: `img`
- **Impact**: Critical

#### Tiger Detail Page
- **Test**: `Tiger detail page should not have accessibility violations`
- **Checks**:
  - Heading hierarchy
  - Image carousel accessible
  - History table semantics
  - Action buttons labeled
  - Metadata organized with proper structure
- **URL**: `/tigers/:id`

---

### 4. Investigation Pages (3 tests)

#### Investigation 2.0 Page
- **Test**: `Investigation 2.0 page should not have accessibility violations`
- **Checks**:
  - File upload area accessible
  - Progress indicators have ARIA live regions
  - Phase tabs keyboard navigable
  - Results properly structured
  - Download buttons labeled
- **URL**: `/investigation2`

#### File Upload Area
- **Test**: `File upload area should have proper labels and instructions`
- **Checks**:
  - File input has associated label
  - Drag-and-drop area has instructions
  - Error messages for invalid files
  - Supported formats listed
  - ARIA attributes on custom upload UI
- **Element**: `input[type="file"]`
- **Impact**: Critical

#### Investigation Results
- **Test**: `Investigation results should have proper structure and headings`
- **Checks**:
  - Heading hierarchy logical
  - Match cards semantically structured
  - Confidence scores have accessible labels
  - Methodology section uses proper lists
  - Citations properly formatted
- **Rule**: `heading-order`

---

### 5. Discovery Pages (2 tests)

#### Discovery Page
- **Test**: `Discovery page should not have accessibility violations`
- **Checks**:
  - Pipeline status indicators accessible
  - Facility list semantically correct
  - Crawl history table accessible
  - Rate limiting info readable
  - Statistics dashboards labeled
- **URL**: `/discovery`

#### Discovery Controls
- **Test**: `Discovery controls should be keyboard accessible`
- **Checks**:
  - Start/stop buttons keyboard accessible
  - Schedule controls accessible
  - Settings form properly labeled
  - All interactive elements focusable
  - No positive tabindex values
- **Element**: `button, [role="button"]`

---

### 6. Facilities Pages (3 tests)

#### Facilities List Page
- **Test**: `Facilities list page should not have accessibility violations`
- **Checks**:
  - List/grid semantic structure
  - Location filters accessible
  - Map/list toggle accessible
  - Facility cards structured
  - Search functionality accessible
- **URL**: `/facilities`

#### Facility Map
- **Test**: `Facility map should have text alternatives`
- **Checks**:
  - Map container has `aria-label` or `role`
  - Markers have accessible names
  - Controls keyboard accessible
  - Zoom controls labeled
  - Alternative text representation available
- **Element**: `.leaflet-container`
- **Impact**: Serious

#### Facility Card Structure
- **Test**: `Facility cards should have semantic structure`
- **Checks**:
  - Cards use proper HTML elements
  - Content hierarchy clear
  - Lists properly marked up
  - Links descriptive
  - Status badges have ARIA labels
- **Rule**: `list`

---

### 7. Verification Queue (2 tests)

#### Verification Queue Page
- **Test**: `Verification queue page should not have accessibility violations`
- **Checks**:
  - Queue items semantically structured
  - Filter controls accessible
  - Sort options accessible
  - Pagination accessible
  - Statistics widgets labeled
- **URL**: `/verification`

#### Verification Action Buttons
- **Test**: `Verification action buttons should have clear labels`
- **Checks**:
  - All buttons have accessible names
  - Icon-only buttons have `aria-label`
  - Approve/reject actions clear
  - Keyboard shortcuts documented
  - Confirmation dialogs accessible
- **Element**: `button`
- **Impact**: Critical

---

### 8. Modal Components (2 tests)

#### Modal Focus Trapping
- **Test**: `Modals should have proper focus trapping`
- **Checks**:
  - `role="dialog"` present
  - `aria-modal="true"` set
  - `aria-labelledby` or `aria-label` present
  - Focus trapped within modal
  - ESC key closes modal
  - Focus returns to trigger element
- **Element**: `[role="dialog"]`
- **Impact**: Critical

#### Modal Close Buttons
- **Test**: `Modal close buttons should be accessible`
- **Checks**:
  - Close button keyboard accessible
  - Close button has accessible name
  - Visual focus indicator
  - Large enough touch target
- **Element**: `[aria-label*="Close"]`
- **Impact**: Serious

---

### 9. Form Components (3 tests)

#### Form Input Labels
- **Test**: `Form inputs should have proper labels`
- **Checks**:
  - Every input has associated label
  - Label properly associated (for/id or wrapping)
  - Placeholder not used as sole label
  - Instructions provided where needed
- **Element**: `input, select, textarea`
- **Rule**: `label`
- **Impact**: Critical

#### Form Validation Errors
- **Test**: `Form validation errors should be announced`
- **Checks**:
  - Error messages have `role="alert"` or `aria-live`
  - Errors associated with inputs (`aria-describedby`)
  - Error summary at top of form
  - Inline errors visible and accessible
  - Errors clearly worded
- **Rule**: `aria-live`
- **Impact**: Critical

#### Required Field Indicators
- **Test**: `Required form fields should be indicated`
- **Checks**:
  - Required inputs have `required` attribute
  - Required inputs have `aria-required="true"`
  - Visual indicator (asterisk) with text alternative
  - Legend explains required field notation
- **Element**: `input[required]`
- **Impact**: Serious

---

### 10. Color Contrast (1 test)

#### All Pages Color Contrast
- **Test**: `All pages should meet color contrast requirements`
- **Pages Tested**:
  - Login (`/login`)
  - Dashboard (`/dashboard`)
  - Tigers (`/tigers`)
  - Facilities (`/facilities`)
  - Investigation (`/investigation2`)
  - Discovery (`/discovery`)
  - Verification (`/verification`)
- **Checks**:
  - Text contrast ratio ≥ 4.5:1 (normal text)
  - Text contrast ratio ≥ 3:1 (large text)
  - UI component contrast ≥ 3:1
  - Focus indicators contrast ≥ 3:1
- **Rule**: `color-contrast`
- **Standard**: WCAG 2.0 Level AA
- **Impact**: Serious

---

### 11. Keyboard Navigation (3 tests)

#### Interactive Elements Keyboard Access
- **Test**: `All interactive elements should be keyboard accessible`
- **Checks**:
  - All links, buttons, inputs reachable via Tab
  - No keyboard traps
  - Custom controls have keyboard handlers
  - Dropdowns keyboard navigable
  - No positive tabindex values
- **Rule**: `keyboard-navigable`
- **Impact**: Critical

#### Skip to Main Content
- **Test**: `Skip to main content link should be present`
- **Checks**:
  - Skip link exists in DOM
  - Skip link visible on focus
  - Skip link is first focusable element
  - Skip link points to `<main>` or `id="main"`
  - Skip link text is descriptive
- **Element**: `a[href="#main"]`
- **Impact**: Moderate
- **Note**: Optional but recommended

#### Logical Tab Order
- **Test**: `Tab order should be logical`
- **Checks**:
  - Tab order follows visual order
  - No positive tabindex values
  - Related controls grouped
  - Tab order doesn't skip important elements
  - Offscreen elements not focusable
- **Rule**: `tabindex`
- **Impact**: Serious

---

### 12. Screen Reader Compatibility (2 tests)

#### Document Structure
- **Test**: `Page should have proper document structure`
- **Checks**:
  - One `<main>` landmark
  - One `<h1>` per page
  - Logical heading hierarchy
  - Navigation in `<nav>`
  - Complementary content in `<aside>`
  - Footer in `<footer>`
- **Rules**: `landmark-one-main`, `region`, `heading-order`
- **Impact**: Moderate

#### Live Regions
- **Test**: `Live regions should be properly marked`
- **Checks**:
  - Dynamic updates use `aria-live`
  - Status messages use `role="status"`
  - Alerts use `role="alert"`
  - Loading indicators use `aria-busy`
  - Progress indicators accessible
- **Element**: `[aria-live]`
- **Impact**: Moderate

---

### 13. Comprehensive Scan Summary (1 test)

#### Full Application Scan
- **Test**: `Generate accessibility report for all critical pages`
- **Pages**: All 7 main pages
- **Output**: Detailed report with:
  - Total violations by impact level
  - Per-page breakdown
  - Violation trends
  - Priority recommendations
- **Impact**: All levels
- **Purpose**: Weekly audit and tracking

---

## Test Coverage Summary

| Category | Tests | Pages/Components | Critical Checks |
|----------|-------|------------------|-----------------|
| Authentication | 2 | 2 pages | Form labels, error messages |
| Navigation | 3 | Header, sidebar | ARIA labels, keyboard access |
| Tigers | 3 | List, detail, images | Alt text, semantic structure |
| Investigation | 3 | Upload, results | File input, headings |
| Discovery | 2 | Pipeline, controls | Keyboard access |
| Facilities | 3 | List, map, cards | Map alternatives, structure |
| Verification | 2 | Queue, actions | Button labels |
| Modals | 2 | Dialogs | Focus trapping, close buttons |
| Forms | 3 | Inputs, validation | Labels, error announcements |
| Color Contrast | 1 | All pages | WCAG AA compliance |
| Keyboard | 3 | All interactions | Tab order, skip link |
| Screen Readers | 2 | Structure, updates | Landmarks, live regions |
| Summary | 1 | Full application | Comprehensive audit |

**Total Tests**: 30 test scenarios
**Total Checks**: 150+ individual accessibility checks

## Violation Impact Levels

Tests focus on **Critical** and **Serious** violations:

- **Critical**: Blocks users completely → **Tests FAIL**
- **Serious**: Significant barriers → **Tests FAIL**
- **Moderate**: Inconvenience → **Tests WARN** (logged but don't fail)
- **Minor**: Annoyance → **Tests WARN** (logged but don't fail)

## WCAG Standards Coverage

All tests check compliance with:
- ✓ WCAG 2.0 Level A (`wcag2a`)
- ✓ WCAG 2.0 Level AA (`wcag2aa`)
- ✓ WCAG 2.1 Level A (`wcag21a`)
- ✓ WCAG 2.1 Level AA (`wcag21aa`)

## Running Specific Test Scenarios

```bash
# Authentication tests
npx playwright test accessibility.spec.ts -g "Authentication"

# Navigation tests
npx playwright test accessibility.spec.ts -g "Navigation"

# Form tests
npx playwright test accessibility.spec.ts -g "Form Components"

# Color contrast tests
npx playwright test accessibility.spec.ts -g "Color Contrast"

# Modal tests
npx playwright test accessibility.spec.ts -g "Modal Components"

# Comprehensive scan
npx playwright test accessibility.spec.ts -g "Comprehensive Scan Summary"
```

## Test Maintenance

When adding new features:

1. Add corresponding accessibility tests
2. Ensure no regressions in existing tests
3. Update this document with new scenarios
4. Run full suite before merging

## Success Criteria

All tests should pass with:
- 0 critical violations
- 0 serious violations
- Moderate/minor violations documented as technical debt
