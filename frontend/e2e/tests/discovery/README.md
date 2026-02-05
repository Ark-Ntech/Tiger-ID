# Discovery Page E2E Tests

Comprehensive end-to-end tests for the Discovery page (`/discovery`) using Playwright.

## Test Coverage

### 1. Page Load and Layout (8 tests)
- ✅ Page displays with header and stats
- ✅ All four stat cards visible (Facilities, Tigers, Images, Crawls)
- ✅ Stat values display correctly
- ✅ Tools used section visible
- ✅ WebSocket connection status badge
- ✅ Scheduler status badge

### 2. Tab Navigation (5 tests)
- ✅ All four tabs visible (Overview, Queue, History, Map)
- ✅ Overview tab active by default
- ✅ Can switch to Queue tab
- ✅ Can switch to History tab
- ✅ Can switch to Map tab

### 3. Overview Tab Content (5 tests)
- ✅ Facility crawl grid displays
- ✅ Scheduler status card shows status
- ✅ Facility breakdown card shows statistics
- ✅ Activity feed visible with live indicator
- ✅ Empty state shown when no active crawls

### 4. Queue Tab Content (3 tests)
- ✅ Queue table or empty message displays
- ✅ Queue count shown
- ✅ Facility rows are clickable

### 5. History Tab Content (3 tests)
- ✅ Crawl history displays
- ✅ History items or empty state shown
- ✅ Status badges on history items

### 6. Map Tab Content (2 tests)
- ✅ Facilities map displays
- ✅ Crawl progress cards shown when facility selected

### 7. Discovery Controls (5 tests)
- ✅ Start/Stop button visible
- ✅ Full crawl button visible
- ✅ Start button click handled
- ✅ Stop button click handled
- ✅ Full crawl button click handled

### 8. Facility Crawl Progress Cards (4 tests)
- ✅ Cards display when available
- ✅ Progress bar visible on cards
- ✅ Facility status shown
- ✅ Cards are clickable

### 9. Activity Feed (8 tests)
- ✅ Feed displays with header
- ✅ Live indicator shown
- ✅ Auto-scroll toggle visible
- ✅ Auto-scroll toggles when clicked
- ✅ Feed list displays
- ✅ Empty state shown if no events
- ✅ Event items display when available
- ✅ Event count shown
- ✅ Event types properly formatted

### 10. WebSocket Updates (2 tests)
- ✅ Handles simulated discovery events
- ✅ Updates crawl status on receiving updates

### 11. Responsive Design (3 tests)
- ✅ Mobile viewport (375x667)
- ✅ Tablet viewport (768x1024)
- ✅ Desktop viewport (1920x1080)

### 12. Error Handling (2 tests)
- ✅ Displays error message if API fails
- ✅ Handles loading state gracefully

### 13. Accessibility (3 tests)
- ✅ Proper ARIA labels on interactive elements
- ✅ Keyboard navigation support
- ✅ Proper heading hierarchy

### 14. Data Persistence (1 test)
- ✅ Tab selection persists across refreshes

## Total Tests: **57 comprehensive test scenarios**

## Running the Tests

### Run all Discovery tests
```bash
cd frontend
npx playwright test e2e/tests/discovery/
```

### Run in headed mode (see browser)
```bash
npx playwright test e2e/tests/discovery/ --headed
```

### Run specific test
```bash
npx playwright test e2e/tests/discovery/discovery.spec.ts -g "should display discovery page"
```

### Run with UI mode (interactive)
```bash
npx playwright test e2e/tests/discovery/ --ui
```

### Debug a specific test
```bash
npx playwright test e2e/tests/discovery/ -g "should handle start button click" --debug
```

### Run on specific browser
```bash
npx playwright test e2e/tests/discovery/ --project=chromium
npx playwright test e2e/tests/discovery/ --project=firefox
npx playwright test e2e/tests/discovery/ --project=webkit
```

### Generate HTML report
```bash
npx playwright test e2e/tests/discovery/
npx playwright show-report
```

## Test Data Requirements

These tests assume:
- Backend API is running at default URL
- Test user credentials: `testuser` / `testpassword`
- Discovery endpoints are accessible
- WebSocket connection available

## Mock Data

Tests use real API responses when available, but also include:
- Mock WebSocket events for real-time update testing
- Simulated crawl status updates
- Error response interception

## Test IDs Used

All components use `data-testid` attributes for stable test selectors:

### Page Level
- `discovery-page` - Main page container
- `discovery-header` - Header section
- `discovery-stats` - Stats grid
- `discovery-tabs` - Tab navigation
- `discovery-loading` - Loading spinner

### Stat Cards
- `stat-facilities` - Facilities stat card
- `stat-tigers` - Tigers stat card
- `stat-images` - Images stat card
- `stat-crawls` - Crawls stat card

### Status Indicators
- `websocket-status` - WebSocket connection badge
- `scheduler-status` - Scheduler status badge

### Tabs
- `tab-overview` - Overview tab button
- `tab-queue` - Queue tab button
- `tab-history` - History tab button
- `tab-map` - Map tab button

### Tab Content
- `tab-content-overview` - Overview tab content
- `tab-content-queue` - Queue tab content
- `tab-content-history` - History tab content
- `tab-content-map` - Map tab content

### Control Buttons
- `start-stop-button` - Start/Stop discovery button
- `full-crawl-button` - Full crawl button

### Facility Crawl Components
- `facility-crawl-grid` - Grid of crawl cards
- `facility-crawl-card-{id}` - Individual facility card
- `facility-progress-bar` - Progress bar
- `facility-status` - Status indicator

### Activity Feed
- `discovery-activity-feed` - Feed container
- `activity-feed-header` - Feed header
- `activity-feed-list` - Event list
- `activity-feed-empty` - Empty state
- `live-indicator` - Live status indicator
- `auto-scroll-toggle` - Auto-scroll toggle
- `event-count` - Event count badge
- `event-item-{id}` - Individual event item
- `event-timestamp-{id}` - Event timestamp
- `event-facility-{id}` - Facility name in event
- `event-message-{id}` - Event message

### Queue/History
- `queue-table` - Queue table
- `queue-empty` - Empty queue message
- `queue-row-{id}` - Queue table row
- `history-item-{id}` - History item
- `history-empty` - Empty history message

### Cards
- `scheduler-status-card` - Scheduler status card
- `facility-breakdown-card` - Facility breakdown card
- `tools-used` - Tools used section
- `crawl-progress-card-{id}` - Crawl progress card

## Best Practices

1. **Use data-testid selectors** - All tests use `data-testid` attributes for stability
2. **Wait for network idle** - Tests wait for `networkidle` state after navigation
3. **Handle loading states** - Tests account for async data loading
4. **Check for both states** - Tests handle both empty and populated data states
5. **Use proper timeouts** - Strategic waits for animations and state updates
6. **Test error scenarios** - API failures are intercepted and tested
7. **Accessibility first** - ARIA attributes and keyboard navigation tested

## CI/CD Integration

These tests are designed to run in CI environments:

```yaml
- name: Run Discovery E2E Tests
  run: |
    cd frontend
    npx playwright install --with-deps
    npx playwright test e2e/tests/discovery/
```

## Debugging Failed Tests

### Screenshot on failure
```bash
npx playwright test e2e/tests/discovery/ --screenshot=only-on-failure
```

### Video recording
```bash
npx playwright test e2e/tests/discovery/ --video=retain-on-failure
```

### Trace viewer
```bash
npx playwright test e2e/tests/discovery/ --trace=on
npx playwright show-trace trace.zip
```

## Related Components

These tests cover the following React components:
- `src/pages/Discovery.tsx` - Main page
- `src/components/discovery/FacilityCrawlGrid.tsx` - Crawl grid
- `src/components/discovery/DiscoveryActivityFeed.tsx` - Activity feed
- `src/components/discovery/CrawlProgressCard.tsx` - Progress cards
- `src/components/discovery/DiscoveryFacilitiesMap.tsx` - Map view

## API Endpoints Tested

- `GET /api/discovery/status` - Discovery scheduler status
- `GET /api/discovery/stats` - Discovery statistics
- `GET /api/discovery/queue` - Crawl queue
- `GET /api/discovery/history` - Crawl history
- `POST /api/discovery/start` - Start discovery
- `POST /api/discovery/stop` - Stop discovery
- `POST /api/discovery/full-crawl` - Trigger full crawl

## WebSocket Events

Tests mock the following WebSocket event types:
- `discovery_event` - General discovery events
- `crawl_update` - Crawl status updates
- Event types: `image_found`, `crawl_started`, `crawl_completed`, `rate_limited`, `error`, `tiger_detected`

## Future Improvements

- [ ] Add tests for map marker interactions
- [ ] Test pagination on queue/history tabs
- [ ] Add tests for filtering/sorting
- [ ] Test real WebSocket connections (not just mocked)
- [ ] Add performance benchmarks
- [ ] Test concurrent crawl handling
- [ ] Add visual regression tests
