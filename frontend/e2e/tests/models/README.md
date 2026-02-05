# Model Comparison E2E Tests

Comprehensive end-to-end tests for the 6-model ensemble comparison features in the Tiger ID Investigation 2.0 workflow.

## Test File

`model-comparison.spec.ts` - Complete E2E test suite for model comparison features

## Test Coverage

### 1. Model Progress Grid (10 tests)

Tests the main model progress visualization during the `stripe_analysis` phase:

- **Display 6 models** - Verifies all 6 ensemble models are shown: wildlife_tools, cvwc2019_reid, transreid, megadescriptor_b, tiger_reid, rapid_reid
- **Grid layout** - Tests responsive grid layout (2x3 mobile, 3x2 tablet, 6x1 desktop)
- **Model cards** - Verifies each model has a card with proper data-testid
- **Grid spacing** - Tests CSS grid template columns are properly applied
- **Responsive design** - Validates layout at different viewport sizes

**Key Selectors:**
- `[data-testid="model-progress-grid"]` - Main grid container
- `[data-testid="model-card-{model}"]` - Individual model cards
- `[data-testid="model-progress-cards"]` - Card container

### 2. Individual Model Progress (10 tests)

Tests progress tracking for each model:

- **Progress percentages** - Validates 0-100% progress display for each model
- **Progress bars** - Tests visual progress bar width matches percentage
- **Progress text** - Verifies text display uses `data-testid="model-progress-text-{model}"`
- **Animated numbers** - Tests AnimatedNumber component shows smooth transitions
- **Progress updates** - Validates real-time WebSocket updates
- **Embedding dimensions** - Shows embedding size per model (1536, 2048, 768, 1024)
- **Processing time** - Displays time in ms or seconds when completed
- **Model weights** - Shows ensemble weight percentage (40%, 30%, 20%, 15%, 10%, 5%)

**Key Selectors:**
- `[data-testid="model-progress-text-{model}"]` - Progress percentage text
- `[data-testid="model-progress-bar-{model}"]` - Progress bar fill
- `[data-testid="model-weight-{model}"]` - Model weight badge
- `[data-testid="model-embeddings-{model}"]` - Embeddings count
- `[data-testid="model-time-{model}"]` - Processing time

### 3. Model Status Indicators (8 tests)

Tests the 4 status states for each model:

**Status States:**
1. **Pending** - Clock icon, gray color, 0% progress
2. **Running** - Spinner icon (animated), tiger-orange color, progress 1-99%
3. **Completed** - Check icon, emerald/green color, 100% progress
4. **Error** - Warning icon, red color, error message displayed

**Tests:**
- Status icon display per state
- Color coding for each status
- Animation for running state (spinning icon)
- Error message display with `data-testid="model-error-{model}"`
- Checkmark icon for completed models

**Key Selectors:**
- `[data-testid="model-status-icon-{model}"]` - Status indicator icon
- `[data-testid="model-error-{model}"]` - Error message text

### 4. Model Completion Count Badge (6 tests)

Tests the "X/6 models complete" badge:

- **Badge display** - Shows completion count in format "X/6"
- **Badge variants** - Success (6/6), danger (has errors), tiger (running), default (pending)
- **Real-time updates** - Badge updates as models complete
- **Dot indicator** - Animated dot when models are running
- **Check icon** - Shows check icon when all complete (6/6)
- **Warning icon** - Shows warning icon when errors present

**Key Selectors:**
- `[data-testid="model-progress-badge"]` - Completion count badge
- `[data-testid="model-progress-title"]` - Grid section title

### 5. Model Retry Functionality (6 tests)

Tests error recovery and retry mechanism:

- **Retry button display** - Shows "Retry" button for errored models
- **Retry button click** - Sends retry request to backend API
- **Loading state** - Disables button and shows spinner during retry
- **Error message** - Displays error text from model
- **Retry callback** - Tests `onRetry` prop callback execution
- **Keyboard accessibility** - Supports Enter/Space key for retry

**Key Selectors:**
- `[data-testid="model-retry-{model}"]` - Retry button
- `[data-testid="model-error-{model}"]` - Error text

### 6. Overall Progress Section (4 tests)

Tests the aggregate progress indicator:

- **Progress bar** - Shows combined progress of all 6 models
- **Progress percentage** - Calculates (completed/total * 100)%
- **Progress label** - "Overall Progress" text
- **Color coding** - Emerald when complete, amber if errors, tiger-orange if running

**Key Selectors:**
- `[data-testid="model-overall-progress-bar"]` - Overall progress bar
- `[data-testid="model-overall-percent"]` - Overall percentage text
- `[data-testid="model-overall-label"]` - "Overall Progress" label

### 7. Model Agreement Badge (6 tests)

Tests model consensus indicator in verification queue:

- **Agreement display** - Shows "X/Y models agree" format
- **High agreement** - 5-6 models (green badge)
- **Medium agreement** - 3-4 models (yellow badge)
- **Low agreement** - 1-2 models (red badge)
- **Threshold** - Agreement threshold set at 0.5 confidence
- **Badge location** - Displayed in verification queue items

**Key Selectors:**
- `[data-testid="model-agreement-badge"]` - Agreement badge
- `[data-testid="agreement-high"]` - High agreement icon
- `[data-testid="agreement-medium"]` - Medium agreement icon
- `[data-testid="agreement-low"]` - Low agreement icon

### 8. Model Score Breakdown (8 tests)

Tests per-model score display in match comparison:

- **Score section** - Displays all 6 model scores
- **Score cards** - Grid of 2-3 columns with model scores
- **Score values** - Shows scores as percentages (0-100%)
- **Sorted order** - Models sorted by score (highest first)
- **Model colors** - Each model has unique color dot
- **Progress bars** - Mini progress bar per model score
- **Model names** - Display names (Wildlife Tools, CVWC 2019, etc.)
- **Highest highlight** - Top scoring model gets highlighted border

**Model Colors:**
- wildlife_tools: Emerald
- cvwc2019_reid: Purple
- transreid: Cyan
- megadescriptor_b: Info blue
- tiger_reid: Amber
- rapid_reid: Gray

**Key Selectors:**
- `[data-testid="model-score-breakdown"]` - Score breakdown section
- `[data-testid="model-score-{model}"]` - Individual model score card
- `[data-testid="highest-score"]` - Highest scoring model indicator

### 9. Comparison Drawer (10 tests)

Tests the slide-out drawer for tiger comparison:

- **Drawer open** - Slides in from right on match click
- **Drawer animation** - Smooth slide-in transition
- **Tiger cards** - Displays up to 4 tigers in 2x2 grid
- **Empty slots** - Shows "+ Add Tiger" placeholders
- **Remove button** - Hover to show remove button per tiger
- **Clear all** - Button to remove all tigers from comparison
- **Export button** - Generate comparison report
- **Close button** - Close drawer (top-right X)
- **Backdrop close** - Click backdrop to close
- **Escape key** - Press Esc to close drawer

**Key Selectors:**
- `[data-testid="comparison-drawer"]` - Drawer panel
- `[data-testid="comparison-drawer-backdrop"]` - Backdrop overlay
- `[data-testid="comparison-drawer-close"]` - Close button
- `[data-testid="comparison-tiger-{id}"]` - Tiger card in drawer
- `[data-testid="comparison-remove-{id}"]` - Remove tiger button
- `[data-testid="comparison-clear-all"]` - Clear all button
- `[data-testid="comparison-export"]` - Export button

### 10. Match Comparison View (12 tests)

Tests side-by-side query vs match comparison:

- **Query image panel** - Left side query image
- **Match image panel** - Right side matched tiger
- **Image containers** - Aspect-square containers with proper sizing
- **Zoom functionality** - Click to zoom/unzoom images
- **Mouse tracking** - Transform origin follows mouse for zoom
- **Stripe overlay toggle** - Show/hide stripe pattern overlay
- **Stripe visibility** - Overlay uses mix-blend-mode for transparency
- **Image metadata** - Shows facility name and capture date
- **Panel focus** - Keyboard arrow keys to switch focus
- **Comparison header** - Shows tiger names and comparison title

**Key Selectors:**
- `[data-testid="match-comparison"]` - Main comparison container
- `[data-testid="query-panel"]` - Query image panel
- `[data-testid="match-panel"]` - Match image panel
- `[data-testid="query-image-container"]` - Query image wrapper
- `[data-testid="match-image-container"]` - Match image wrapper
- `[data-testid="query-image"]` - Query img element
- `[data-testid="match-image"]` - Match img element
- `[data-testid="query-stripe-toggle"]` - Query stripe toggle button
- `[data-testid="match-stripe-toggle"]` - Match stripe toggle button
- `[data-testid="query-stripe-overlay"]` - Query stripe overlay
- `[data-testid="match-stripe-overlay"]` - Match stripe overlay

### 11. Confidence Display (10 tests)

Tests confidence score visualization with color coding:

**Confidence Levels:**
- **High (≥85%)**: Emerald/green color
- **Medium (65-85%)**: Amber/yellow color
- **Low-Medium (40-65%)**: Orange color
- **Low (<40%)**: Red color

**Tests:**
- Overall confidence score display
- Confidence progress bar with color
- Color coding per level
- Confidence section layout
- Model agreement split view
- Confidence bar animation
- Percentage text formatting
- Normalized score handling (0-1 or 0-100)

**Key Selectors:**
- `[data-testid="confidence-section"]` - Confidence display section
- `[data-testid="confidence-bar-fill"]` - Progress bar fill element
- `[data-testid="overall-confidence"]` - Overall confidence text

### 12. Verification Actions (8 tests)

Tests verification workflow actions:

- **Verification status badge** - Shows "Verified" or "Rejected" status
- **Verify button** - Green button with check icon
- **Reject button** - Red button with X icon
- **Button states** - Enabled/disabled based on context
- **Action callbacks** - Tests onVerify prop callback
- **Status update** - Badge updates after verification
- **Button styling** - Proper Tailwind classes applied
- **Focus states** - Keyboard focus rings visible

**Key Selectors:**
- `[data-testid="verification-status"]` - Status badge
- `[data-testid="verify-match-button"]` - Verify button
- `[data-testid="reject-match-button"]` - Reject button
- `[data-testid="comparison-close"]` - Close comparison button

### 13. Keyboard Navigation (6 tests)

Tests keyboard shortcuts for accessibility:

**Shortcuts:**
- **Escape** - Close comparison/drawer
- **Arrow Left** - Focus query image panel
- **Arrow Right** - Focus match image panel
- **Space/Enter** - Toggle stripe overlay for focused panel
- **Z** - Toggle zoom for focused panel
- **Tab** - Navigate between elements

**Tests:**
- Escape key closes modals
- Arrow keys switch panel focus
- Space toggles stripe overlay
- Z key zooms focused image
- Focus indicators visible
- Keyboard hints displayed

### 14. Responsive Layout (6 tests)

Tests responsive design at different viewport sizes:

**Breakpoints:**
- **Mobile (375px)**: 2 columns (2x3 for 6 models)
- **Tablet (768px)**: 3 columns (3x2 for 6 models)
- **Desktop (1920px)**: 6 columns (6x1 for 6 models)

**Tests:**
- Mobile grid layout (grid-cols-2)
- Tablet grid layout (sm:grid-cols-3)
- Desktop grid layout (lg:grid-cols-6)
- Comparison images stack on mobile
- Drawer full-width on mobile
- Text truncation on small screens

### 15. Accessibility (6 tests)

Tests WCAG 2.0/2.1 compliance:

- **ARIA labels** - Progress bars have aria-label
- **Role attributes** - dialog role on comparison
- **Button labels** - Descriptive text on all buttons
- **Keyboard focus** - Visible focus indicators
- **Color contrast** - Text meets AA standards
- **Screen readers** - Semantic HTML structure

**ARIA Attributes:**
- `role="progressbar"` on progress bars
- `aria-valuenow`, `aria-valuemin`, `aria-valuemax` on progress
- `aria-label` on close buttons
- `role="dialog"` on comparison drawer
- `aria-labelledby` for dialog titles

### 16. Model Comparison Integration (2 tests)

Tests complete end-to-end workflow:

- **Full workflow** - Upload → stripe_analysis → complete → comparison
- **State coordination** - All model features work together
- **Phase transitions** - Proper state updates between phases
- **Real-time updates** - WebSocket updates reflected in UI

## Test Data

### Mock Model Progress

```typescript
{
  wildlife_tools: { status: 'completed', progress: 100, embedding_dim: 1536 },
  cvwc2019_reid: { status: 'running', progress: 67, embedding_dim: 2048 },
  transreid: { status: 'pending', progress: 0, embedding_dim: 768 },
  megadescriptor_b: { status: 'pending', progress: 0, embedding_dim: 1024 },
  tiger_reid: { status: 'error', progress: 0, embedding_dim: 2048, error: 'Connection timeout' },
  rapid_reid: { status: 'pending', progress: 0, embedding_dim: 2048 }
}
```

## Running Tests

### Run all model comparison tests
```bash
npx playwright test tests/models/model-comparison
```

### Run specific test groups
```bash
# Model progress grid tests only
npx playwright test tests/models/model-comparison -g "Model Progress Grid"

# Model status indicators only
npx playwright test tests/models/model-comparison -g "Model Status Indicators"

# Comparison drawer tests only
npx playwright test tests/models/model-comparison -g "Comparison Drawer"

# Confidence display tests only
npx playwright test tests/models/model-comparison -g "Confidence Display"
```

### Run in headed mode (see browser)
```bash
npx playwright test tests/models/model-comparison --headed
```

### Run in debug mode
```bash
npx playwright test tests/models/model-comparison --debug
```

### Run with specific browser
```bash
npx playwright test tests/models/model-comparison --project=chromium
npx playwright test tests/models/model-comparison --project=firefox
npx playwright test tests/models/model-comparison --project=webkit
```

## Test Helpers

### Authentication
Uses `login()` helper from `../../helpers/auth.ts` to authenticate before each test.

### Phase Waiting
`waitForPhase()` helper polls investigation status until specific phase is reached.

### Investigation Start
`startInvestigation()` helper uploads image and returns investigation ID.

## Component Architecture

### ModelProgressGrid Component

**Location:** `frontend/src/components/investigations/progress/ModelProgressGrid.tsx`

**Props:**
- `models: ModelProgress[]` - Array of 6 model progress objects
- `title?: string` - Grid section title (default: "Stripe Analysis")
- `className?: string` - Additional CSS classes
- `onRetry?: (model: string) => void` - Retry callback for errored models

**Features:**
- Responsive grid layout with Tailwind breakpoints
- AnimatedNumber component for smooth percentage transitions
- Status icons with color coding
- Progress bars with animated width
- Model weights as percentage badges
- Error states with retry buttons
- Overall progress indicator

### ComparisonDrawer Component

**Location:** `frontend/src/components/investigations/comparison/ComparisonDrawer.tsx`

**Props:**
- `isOpen: boolean` - Drawer visibility state
- `onClose: () => void` - Close callback
- `tigers: TigerComparison[]` - Array of tigers to compare (max 4)
- `maxTigers?: number` - Maximum tigers allowed (default: 4)
- `onRemoveTiger?: (tigerId: string) => void` - Remove callback
- `onClearAll?: () => void` - Clear all callback
- `onExport?: () => void` - Export callback

**Features:**
- Headless UI Dialog with transitions
- Slide-in from right animation
- 2x2 grid for up to 4 tigers
- Image zoom on hover
- Confidence badges with color coding
- Model badges with color per model
- Empty slots for adding more tigers
- Export comparison report button

### MatchComparison Component

**Location:** `frontend/src/components/investigations/results/cards/MatchComparison.tsx`

**Props:**
- `queryImage: ComparisonImage` - Uploaded query image
- `matchImage: ComparisonImage` - Database match candidate
- `confidence: number` - Overall confidence score (0-1 or 0-100)
- `modelScores?: Record<string, number>` - Per-model scores
- `isVerified?: boolean` - Verification status
- `onVerify?: (verified: boolean) => void` - Verify callback
- `onClose?: () => void` - Close callback
- `showStripeOverlay?: boolean` - Enable stripe toggle (default: true)

**Features:**
- Side-by-side image comparison
- Click to zoom with mouse tracking
- Stripe pattern overlay toggle
- Model score breakdown
- Model agreement indicator
- Confidence progress bar with color coding
- Keyboard navigation (arrows, space, Z, Esc)
- Verify/Reject action buttons

## Total Test Count

**116 tests** across 16 test suites covering all model comparison features.

## CI/CD Integration

Tests are optimized for CI with:
- 2 retries per test
- 30-60 second timeouts for long-running operations
- API route mocking for deterministic tests
- Screenshot capture on failure
- JUnit XML report generation

## Future Enhancements

- [ ] Add visual regression tests for model cards
- [ ] Test WebSocket reconnection scenarios
- [ ] Add performance tests for large model counts
- [ ] Test mobile touch gestures for zoom
- [ ] Add tests for model calibration temperature
- [ ] Test ensemble strategy switching (weighted/staggered/parallel)
- [ ] Add tests for model fallback behavior
- [ ] Test concurrent model execution visualization
