# Dashboard E2E Tests

Comprehensive end-to-end tests for the Tiger ID Dashboard page using Playwright.

## Test File

- **Location**: `frontend/e2e/tests/dashboard/dashboard.spec.ts`
- **Total Tests**: 64 test scenarios organized in 12 describe blocks

## Test Coverage

### 1. Page Load and Structure (2 tests)
- Verifies dashboard page loads with all sections
- Checks for header, stats grid, main content, and analytics tabs
- Validates last updated timestamp display

### 2. Quick Stats Grid (7 tests)
- Tests display of all 4 stat cards
- Verifies individual stats:
  - Total Tigers (with trend indicators)
  - Facilities
  - ID Rate (percentage display)
  - Pending Verifications
- Validates trend indicators (increase/decrease/neutral)
- Tests clickable stat cards and navigation

### 3. Time Range Selector (3 tests)
- Tests presence of 7d/30d/90d buttons
- Verifies active state indicator (ring-2 class)
- Validates analytics data updates on range change

### 4. Refresh Button (3 tests)
- Tests refresh button display and functionality
- Verifies loading state during refresh
- Checks spinning icon animation
- Validates last updated timestamp changes

### 5. Subagent Activity Panel (7 tests)
- Tests panel display and title
- Validates pool utilization stats (ML inference, research, report generation)
- Tests utilization bars with progress percentages
- Verifies active tasks list display
- Tests empty state when no tasks
- Validates task status indicators (running/queued/completed/error)
- Tests task click navigation to investigation

### 6. Recent Investigations Table (5 tests)
- Tests table/empty state display
- Validates investigation row structure (image, date, status, matches, actions)
- Tests row click navigation
- Verifies view button functionality
- Tests "View All" button navigation

### 7. Geographic Map (3 tests)
- Tests map card display
- Validates map or empty state rendering
- Checks Leaflet map container when data exists

### 8. Analytics Tabs (9 tests)
- Tests all 7 tab buttons visibility
- Validates default tab (Investigations)
- Tests tab switching:
  - Investigations
  - Evidence & Verification
  - Geographic
  - Tigers
  - Facilities
  - Agent Performance
  - Model Performance
- Validates tab content display
- Tests model performance tab specific elements

### 9. Charts and Visualizations (7 tests)
- Tests investigation activity chart
- Validates line chart rendering
- Checks pie charts in Investigations tab
- Tests bar charts in various tabs
- Validates tiger identification charts
- Tests model performance charts
- Validates loading states for charts

### 10. Responsive Behavior (3 tests)
- Tests mobile layout (375x667)
- Validates tablet layout (768x1024)
- Tests desktop layout (1920x1080)

### 11. Navigation (3 tests)
- Tests navigation from Tigers stat card
- Tests navigation from Facilities stat card
- Tests navigation from Pending Verifications stat card

### 12. Error Handling (2 tests)
- Tests graceful API error handling
- Validates empty states instead of error messages

## Data Test IDs Used

### Main Sections
- `dashboard-page`
- `dashboard-header`
- `dashboard-controls`
- `dashboard-main-content`
- `dashboard-secondary-content`

### Quick Stats
- `quick-stats-grid`
- `stat-total-tigers`
- `stat-facilities`
- `stat-id-rate`
- `stat-pending-verifications`
- `stat-value`
- `stat-change`

### Subagent Panel
- `subagent-activity-panel`
- `subagent-pool-stats`
- `subagent-pool-ml_inference`
- `subagent-pool-research`
- `subagent-pool-report_generation`
- `subagent-tasks-list`
- `subagent-task-{id}`

### Investigations Table
- `recent-investigations-card`
- `investigations-table`
- `investigations-table-loading`
- `investigations-table-empty`
- `investigation-row-{id}`
- `query-image-thumbnail`
- `investigation-date`
- `investigation-status`
- `investigation-match-count`
- `investigation-top-match`
- `investigation-actions`
- `view-investigation-{id}`

### Geographic Map
- `geographic-map-card`

### Analytics Tabs
- `analytics-tabs`
- `tab-investigations`
- `tab-evidence-&-verification`
- `tab-geographic`
- `tab-tigers`
- `tab-facilities`
- `tab-agent-performance`
- `tab-model-performance`
- `investigation-analytics-tab`
- `evidence-verification-tab`
- `geographic-tab`
- `tiger-analytics-tab`
- `facility-analytics-tab`
- `agent-analytics-tab`
- `model-performance-tab`

### Model Performance
- `model-select`
- `benchmark-button`
- `model-performance-table`
- `model-row-{model}`
- `model-info-{model}`
- `benchmark-results`

### Charts
- `investigation-activity-chart`

### Controls
- `refresh-button`
- `toggle-filters`
- `status-filter`
- `filter-{status}`

## Running the Tests

### Run all dashboard tests
```bash
npx playwright test tests/dashboard/dashboard
```

### Run in headed mode
```bash
npx playwright test tests/dashboard/dashboard --headed
```

### Run specific test
```bash
npx playwright test tests/dashboard/dashboard -g "should display dashboard page"
```

### Debug mode
```bash
npx playwright test tests/dashboard/dashboard --debug
```

### Run with specific browser
```bash
npx playwright test tests/dashboard/dashboard --project=chromium
```

## Test Scenarios Covered

### Happy Paths
- ✅ All sections load successfully
- ✅ Stats display correct data
- ✅ Time range filtering works
- ✅ Refresh updates all data
- ✅ Navigation from various entry points
- ✅ Charts render without errors
- ✅ Tab switching works smoothly

### Edge Cases
- ✅ Empty state when no investigations
- ✅ Empty state when no tasks
- ✅ Empty state when no facility data
- ✅ Filtered results showing no matches
- ✅ Loading states for all async data

### Error Handling
- ✅ API errors don't block UI
- ✅ Missing data shows empty states
- ✅ Error modals are dismissible

### Responsive Design
- ✅ Mobile layout (375px width)
- ✅ Tablet layout (768px width)
- ✅ Desktop layout (1920px width)

### User Interactions
- ✅ Click stat cards to navigate
- ✅ Click investigation rows to view details
- ✅ Click tasks to view investigations
- ✅ Click facilities on map
- ✅ Switch between analytics tabs
- ✅ Change time ranges
- ✅ Refresh data manually

## Dependencies

The dashboard tests rely on:
- Authentication helper (`helpers/auth.ts`)
- QuickStatsGrid component
- SubagentActivityPanel component
- RecentInvestigationsTable component
- GeographicMap component
- Recharts library for chart rendering

## Notes

### Timing Considerations
- Uses `waitForTimeout` strategically for async operations
- Most waits are set to 1000-1500ms for data loading
- Chart rendering may take up to 2000ms

### Authentication
- All tests run after authentication via `login()` helper
- Tests assume valid user credentials

### Data Dependencies
- Tests handle both populated and empty states
- No hardcoded data expectations
- Flexible assertions for dynamic content

### Browser Compatibility
- Tests run on Chromium, Firefox, and WebKit
- Responsive tests validate different viewports
- Chart rendering tested across browsers

## Future Enhancements

- [ ] Add tests for real-time data updates
- [ ] Test WebSocket connections for live stats
- [ ] Add tests for auto-refresh functionality
- [ ] Test export functionality for analytics
- [ ] Add performance benchmarks for chart rendering
- [ ] Test accessibility of all interactive elements
- [ ] Add visual regression tests for charts
- [ ] Test keyboard navigation through dashboard
