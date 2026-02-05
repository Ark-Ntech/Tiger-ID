# Facility Tests

Comprehensive E2E tests for facility management features.

## Test Files

### `facility-detail.spec.ts`

Tests for the Facility Detail page, covering all aspects of viewing and managing individual facilities.

**Test Scenarios:**

1. **View facility detail** - Page loads with complete facility information
2. **Facility map** - Shows facility location on map view with Leaflet
3. **Crawl history timeline** - Displays crawl events and history
4. **Timeline event details** - Expanding shows images found, duration, errors
5. **Tiger gallery** - Shows tigers associated with this facility
6. **Gallery view modes** - Toggle between grid/list view
7. **Group by tiger** - Grouping toggle functionality
8. **Click tiger** - Navigates to tiger detail page
9. **Edit facility** - Can edit facility information
10. **Start crawl** - Can trigger manual crawl

**Additional Coverage:**

- Discovery status monitoring
- Facility metadata and timestamps
- Links and social media display
- Accreditation and inspection info
- Navigation back to facilities list
- Reference facility badge
- Capacity and tiger statistics
- Loading states
- Empty states
- Error handling (facility not found)
- Mobile-responsive detail panel
- Filter functionality
- Show more events pagination
- Image quality indicators
- Navigation flow testing

## Data Test IDs

The tests rely on the following `data-testid` attributes:

### Page Level
- `facilities-page` - Main facilities list page container
- `facility-detail-page` - Main facility detail page container (full page)
- `facility-detail-panel` - Detail panel (sidebar)
- `facility-detail-panel-mobile` - Mobile detail panel (bottom sheet)

### Facility List
- `facilities-list` - Facilities list container
- `facilities-empty` - Empty state message
- `facilities-loading` - Loading spinner
- `facilities-error` - Error state message
- `facility-card-{id}` - Individual facility cards
- `add-facility-button` - Add new facility button

### Facility Information
- `facility-info-*` - Facility information sections
- `view-facility-details` - Button to navigate to full detail page
- `close-detail-panel` - Close detail panel button
- `close-detail-panel-mobile` - Mobile close button

### View Controls
- `view-mode-toggle` - Container for view mode buttons
- `view-mode-list` - List view button
- `view-mode-map` - Map view button

### Map
- `facilities-map-container` - Map container
- `facility-map-view` - Map component
- `.leaflet-container` - Leaflet map element (class selector)
- `.leaflet-control-zoom` - Map zoom controls (class selector)

### Crawl History
- `crawl-history-timeline` - Timeline component container
- `crawl-summary-stats` - Summary statistics section
- `crawl-events-list` - Events list container
- `crawl-history-empty` - Empty state for no events
- `crawl-history-loading` - Loading indicator
- `crawl-history-load-more` - Load more button (server pagination)
- `crawl-history-show-more` - Show more/less toggle (local pagination)
- `crawl-event-{id}` - Individual crawl event items
- `timeline-connector` - Timeline vertical line
- `event-icon-{type}` - Event type icon
- `event-badge-{type}` - Event type badge
- `event-timestamp` - Event timestamp text
- `event-details` - Expandable details section
- `detail-duration` - Crawl duration field
- `detail-image-count` - Images found field
- `detail-tiger-count` - Tigers detected field
- `detail-wait-time` - Rate limit wait time field
- `detail-error-message` - Error message field
- `detail-timestamp` - Full timestamp field
- `discovery-status` - Discovery status indicator
- `start-crawl` - Manual crawl trigger button

### Tiger Gallery
- `facility-tiger-gallery` - Tiger gallery component
- `gallery-title` - Gallery title heading
- `gallery-subtitle` - Gallery subtitle (image count)
- `gallery-empty-state` - Empty state message
- `gallery-skeleton` - Loading skeleton
- `view-mode-toggle` - View mode toggle buttons
- `group-by-toggle` - Tiger grouping checkbox
- `flat-gallery` - Flat (ungrouped) gallery view
- `grouped-gallery` - Grouped gallery view
- `tiger-section` - Tiger section container (when grouped)
- `tiger-section-header` - Tiger section header button
- `tiger-section-name` - Tiger name in section header
- `tiger-section-content` - Tiger section content
- `image-card` - Individual image card (grid view)
- `image-row` - Individual image row (list view)
- `tiger-name-link` - Clickable tiger name
- `quality-overlay` - Image quality indicator overlay
- `quality-badge` - Image quality badge

### Filters
- `facility-filters` - Filters component container

## Running Tests

### Run all facility tests
```bash
npx playwright test tests/facilities/
```

### Run facility detail tests only
```bash
npx playwright test tests/facilities/facility-detail
```

### Run specific test
```bash
npx playwright test tests/facilities/facility-detail -g "should display facility detail page"
```

### Run in headed mode
```bash
npx playwright test tests/facilities/facility-detail --headed
```

### Run in UI mode (interactive)
```bash
npx playwright test tests/facilities/facility-detail --ui
```

### Run with debugging
```bash
npx playwright test tests/facilities/facility-detail --debug
```

## Test Coverage

### Core Functionality ✅
- [x] Facility detail page loading
- [x] Facility information display
- [x] Map visualization with Leaflet
- [x] Crawl history timeline
- [x] Tiger gallery with lazy loading
- [x] Filter functionality

### Interactions ✅
- [x] View mode toggles (list/grid)
- [x] Tiger grouping checkbox
- [x] Navigation to tiger details
- [x] Manual crawl triggers
- [x] Edit functionality
- [x] Event expansion/collapse
- [x] Show more/less events

### Status & Monitoring ✅
- [x] Discovery status badges
- [x] Crawl event details (duration, images, tigers, errors)
- [x] Accreditation badges
- [x] Reference facility indicators
- [x] Quality indicators on images

### Error Handling ✅
- [x] Loading states
- [x] Empty states
- [x] Facility not found
- [x] API errors

### Responsive Design ✅
- [x] Mobile detail panel (bottom sheet)
- [x] Responsive layout
- [x] Mobile close button

## Component Architecture

### CrawlHistoryTimeline Component
**File**: `frontend/src/components/facilities/CrawlHistoryTimeline.tsx`

**Props**:
- `events: CrawlEvent[]` - Array of crawl events
- `facilityId: string` - Facility identifier
- `maxEvents?: number` - Maximum events to show before pagination
- `onLoadMore?: () => void` - Callback for loading more events
- `hasMore?: boolean` - Whether more events exist
- `isLoading?: boolean` - Loading state

**Event Types**:
- `crawl_started` - Crawl initiated
- `crawl_completed` - Crawl finished successfully
- `images_found` - Images discovered
- `tigers_detected` - Tigers identified
- `rate_limited` - Rate limit hit
- `error` - Crawl failed

**Features**:
- Chronological timeline with icons and badges
- Expandable event details
- Summary statistics (completed crawls, tigers found, errors)
- Show more/less functionality for local pagination
- Load more button for server pagination
- Empty state

### FacilityTigerGallery Component
**File**: `frontend/src/components/facilities/FacilityTigerGallery.tsx`

**Props**:
- `facilityId: string` - Facility identifier
- `facilityName: string` - Facility name
- `images: TigerImage[]` - Array of tiger images
- `onImageClick?: (image: TigerImage) => void` - Image click handler
- `onTigerClick?: (tigerId: string) => void` - Tiger name click handler
- `viewMode?: 'grid' | 'list'` - Display mode
- `groupByTiger?: boolean` - Whether to group by tiger
- `isLoading?: boolean` - Loading state

**Features**:
- Grid and list view modes
- Group by tiger with collapsible sections
- Lazy-loaded images with intersection observer
- Quality indicators and confidence badges
- Tiger name links
- Empty state with icon
- Loading skeleton

### FacilityMapView Component
**File**: `frontend/src/components/facilities/FacilityMapView.tsx`

**Features**:
- Leaflet map integration
- Facility markers with info popups
- Map controls (zoom, layers)
- Responsive map container

### FacilityFilters Component
**File**: `frontend/src/components/facilities/FacilityFilters.tsx`

**Features**:
- Search input
- Type filters (zoo, sanctuary, rescue, breeding)
- Country filters
- Discovery status filters
- Has tigers filter

## Best Practices

1. **Use data-testid selectors** for reliable element selection
2. **Wait for elements** instead of using arbitrary timeouts
3. **Test happy paths and edge cases** (facility not found, no tigers, empty states)
4. **Verify navigation** ensure URLs change correctly
5. **Check loading states** ensure proper UX during data fetching
6. **Test responsive behavior** mobile and desktop views
7. **Test interactions** clicks, toggles, expansions
8. **Verify accessibility** ARIA labels, keyboard navigation

## Implementation Checklist

To ensure tests pass, the Facility Detail page should include:

### Required Elements
- [x] Page with `data-testid="facilities-page"`
- [x] Facility cards with `data-testid="facility-card-{id}"`
- [x] Detail panel with `data-testid="facility-detail-panel"`
- [x] Map view with `data-testid="facilities-map-container"`
- [x] Crawl history with `data-testid="crawl-history-timeline"`
- [x] Tiger gallery with `data-testid="facility-tiger-gallery"`

### Required Buttons
- [x] "View Full Details" with `data-testid="view-facility-details"`
- [x] "Start Crawl" or similar with `data-testid="start-crawl"`
- [x] "Edit" button with `data-testid="edit-facility"`
- [x] Close panel with `data-testid="close-detail-panel"`
- [x] View mode toggles with `data-testid="view-mode-list"` and `data-testid="view-mode-map"`

### Required Status Indicators
- [x] Discovery status with `data-testid="discovery-status"`
- [x] Accreditation badges
- [x] Reference facility badge
- [x] Quality indicators on images

### Required Interactive Elements
- [x] View mode toggles with proper `aria-pressed` states
- [x] Tiger grouping checkbox with `data-testid="group-by-toggle"`
- [x] Clickable image cards with `data-testid="image-card"`
- [x] Expandable crawl events with `data-testid="crawl-event-{id}"`
- [x] Tiger name links with `data-testid="tiger-name-link"`

### Required States
- [x] Loading state with `data-testid="facilities-loading"`
- [x] Error state with `data-testid="facilities-error"`
- [x] Empty state with `data-testid="facilities-empty"`
- [x] Gallery empty state with `data-testid="gallery-empty-state"`
- [x] Timeline empty state with `data-testid="crawl-history-empty"`

## Test Data Requirements

### Prerequisites
- Backend API running on `http://localhost:8000`
- Frontend dev server running on `http://localhost:5173`
- Test user credentials in `.env`:
  - `TEST_USER_EMAIL=testuser`
  - `TEST_USER_PASSWORD=testpassword`
- At least one facility record in database

### Recommended Test Data
- **Facility with tigers**: For testing gallery and grouping
- **Facility with crawl history**: For testing timeline and events
- **Facility with location (lat/long)**: For testing map visualization
- **Facility with website/social links**: For testing link display
- **Facility with accreditation**: For testing badge display
- **Reference facility**: For testing reference badge

## Troubleshooting

### Tests failing with "Element not found"
- Ensure `data-testid` attributes are present in components
- Check if elements are conditionally rendered
- Add proper wait conditions: `await page.waitForSelector('[data-testid="element"]')`
- Use `page.locator().count()` to check if element exists before interacting

### Tests timing out
- Increase timeout for slow API calls: `test.setTimeout(60000)`
- Check if backend API is running
- Verify authentication is working properly
- Check network tab for failed requests

### Flaky tests
- Replace `waitForTimeout` with `waitForSelector` or `waitForLoadState`
- Ensure test data is consistent between runs
- Check for race conditions in async operations
- Use `page.waitForResponse()` for API calls

### Map not loading
- Verify Leaflet CSS and JS are loaded
- Check for console errors in browser
- Ensure facility has valid latitude/longitude
- Increase wait time after switching to map view

### Images not displaying
- Verify image URLs are valid
- Check CORS settings on image server
- Test lazy loading intersection observer
- Check for console errors about failed image loads

## Debugging Tips

1. **Run with headed mode** to see browser actions:
   ```bash
   npx playwright test tests/facilities/facility-detail --headed
   ```

2. **Use UI mode** for interactive debugging:
   ```bash
   npx playwright test tests/facilities/facility-detail --ui
   ```

3. **Add screenshots** on failure (automatic in CI)

4. **Generate trace files** for detailed debugging:
   ```bash
   npx playwright test tests/facilities/facility-detail --trace on
   ```

5. **View trace**:
   ```bash
   npx playwright show-trace trace.zip
   ```

## Future Enhancements

- [ ] Add tests for facility edit form validation
- [ ] Test crawl scheduling configuration
- [ ] Add tests for bulk facility actions
- [ ] Test image preview and lightbox functionality
- [ ] Add performance benchmarks for large galleries
- [ ] Test WebSocket updates for live crawl status
- [ ] Add visual regression tests for facility cards
- [ ] Test map clustering for many facilities
- [ ] Add accessibility tests (WCAG compliance)
- [ ] Test export/import facility data
- [ ] Test facility comparison view
- [ ] Add tests for advanced filters

## Related Documentation

- [Main E2E README](../../README.md)
- [Tiger Detail Tests](../tigers/README.md)
- [Investigation Tests](../../investigation-flow.spec.ts)
- [Discovery Tests](../../discovery-flow.spec.ts)
- [Architecture Docs](../../../../docs/ARCHITECTURE.md)
- [Discovery Pipeline Docs](../../../../docs/DISCOVERY_PIPELINE.md)
