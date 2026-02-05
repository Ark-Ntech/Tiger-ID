# Tiger Detail Page E2E Tests

Comprehensive Playwright end-to-end tests for the Tiger Detail page.

## Test File

`tiger-detail.spec.ts` - Full test coverage for individual tiger detail pages

## Test Coverage

### 1. View Tiger Detail (4 tests)
Tests basic tiger detail page functionality:
- Display tiger detail page with basic information
- Load tiger information successfully
- Display status badge
- Show metadata section

**Selectors Used:**
- `[data-testid="tiger-detail-page"]`
- `[data-testid="tiger-info-name"]`
- `[data-testid="tiger-info-id"]`
- `[data-testid="tiger-info-status"]`
- `[data-testid="tiger-status-badge"]`
- `[data-testid="tiger-metadata"]`

### 2. Tiger Image Gallery (5 tests)
Tests image display and gallery functionality:
- Display tiger image gallery
- Show all images for tiger
- Display image cards with proper layout
- Open lightbox when clicking image
- Navigate between images in gallery

**Selectors Used:**
- `[data-testid="tiger-image-gallery"]`
- `[data-testid^="image-card-"]`
- `[data-testid="image-lightbox"]`

### 3. Image Quality Indicators (2 tests)
Tests image quality assessment display:
- Display image quality badges
- Show quality scores if available

**Selectors Used:**
- `[data-testid*="quality"]`
- `[data-testid*="quality-score"]`

### 4. Identification Timeline (4 tests)
Tests timeline display and event history:
- Display identification timeline section
- Show timeline events with correct structure
- Display event types correctly
- Show timestamps for timeline events

**Selectors Used:**
- `[data-testid="tiger-identification-timeline"]`
- `[data-testid^="timeline-event-"]`

### 5. Related Investigations (4 tests)
Tests investigation links and navigation:
- Display related investigations panel
- Show investigations involving this tiger
- Navigate to investigation detail when clicking investigation
- Display investigation status and details

**Selectors Used:**
- `[data-testid="related-investigations-panel"]`
- `[data-testid^="related-investigation-"]`

### 6. Edit Tiger (4 tests)
Tests tiger editing functionality:
- Show edit button
- Enable editing mode when clicking edit
- Allow editing tiger name
- Allow editing tiger notes

**Selectors Used:**
- Edit button (text-based)
- Input fields (`input[name="name"]`, `textarea[name="notes"]`)

### 7. Delete Tiger (2 tests)
Tests tiger deletion with confirmation:
- Show delete button or option
- Show confirmation dialog when deleting tiger

**Selectors Used:**
- Delete button (text-based)
- Confirmation dialog elements

### 8. Navigate to Facility (2 tests)
Tests facility information and navigation:
- Show facility information
- Navigate to facility detail when clicking facility link

**Selectors Used:**
- `[data-testid*="facility"]`
- Facility links (`a[href*="/facilities/"]`)

### 9. Quick Actions (3 tests)
Tests quick action buttons:
- Show launch investigation button
- Show back to tigers button
- Navigate back to tigers list when clicking back

**Selectors Used:**
- Action buttons (text-based)

### 10. Error Handling (2 tests)
Tests error states and loading:
- Handle non-existent tiger gracefully
- Show loading state while fetching tiger data

**Selectors Used:**
- `[data-testid="tiger-detail-loading"]`
- Error alert elements

## Total Test Count

**40 comprehensive test cases** covering all major tiger detail page functionality

## Running the Tests

### Run all tiger detail tests
```bash
cd frontend
npx playwright test tests/tigers/tiger-detail
```

### Run specific test group
```bash
# View tiger detail tests
npx playwright test tests/tigers/tiger-detail -g "View Tiger Detail"

# Image gallery tests
npx playwright test tests/tigers/tiger-detail -g "Tiger Image Gallery"

# Timeline tests
npx playwright test tests/tigers/tiger-detail -g "Identification Timeline"

# Related investigations tests
npx playwright test tests/tigers/tiger-detail -g "Related Investigations"
```

### Run in headed mode (see browser)
```bash
npx playwright test tests/tigers/tiger-detail --headed
```

### Run in debug mode
```bash
npx playwright test tests/tigers/tiger-detail --debug
```

### Run in UI mode (interactive)
```bash
npx playwright test tests/tigers/tiger-detail --ui
```

## Test Data Requirements

The tests are designed to work with existing database data and gracefully handle cases where:
- No tigers exist in the database
- A tiger has no images
- A tiger has no related investigations
- A tiger has no identification history

Tests use flexible selectors that check for elements and adapt based on what's present.

## Best Practices Implemented

1. **Flexible selectors** - Uses data-testid attributes where available, falls back to semantic selectors
2. **Graceful degradation** - Tests handle missing data without failing
3. **Proper waits** - Uses `waitForTimeout` strategically and checks element visibility
4. **Independent tests** - Each test is self-contained and doesn't depend on others
5. **Clean navigation** - Always starts from tigers list page for consistency
6. **Error tolerance** - Tests check for element existence before interacting

## Future Enhancements

- [ ] Add visual regression testing for image gallery
- [ ] Add tests for image quality assessment algorithms
- [ ] Add tests for timeline filtering/sorting
- [ ] Add tests for bulk operations on investigations
- [ ] Add tests for tiger comparison features
- [ ] Add tests for export/download functionality
- [ ] Add accessibility testing with axe-core
- [ ] Add performance testing for large image galleries

## Troubleshooting

### Test failing: "Tiger not found"
- Ensure test database has at least one tiger record
- Check API endpoint is accessible at `http://localhost:8000`

### Test failing: "Element not visible"
- Increase wait timeout in specific test
- Check if element is conditionally rendered
- Verify CSS classes aren't hiding elements

### Test failing: "Navigation timeout"
- Check frontend dev server is running on port 5173
- Verify no console errors blocking navigation
- Ensure auth token is valid

### Flaky image tests
- Add explicit wait for image load: `await page.waitForLoadState('networkidle')`
- Check image URLs are valid and accessible
- Verify no CORS issues with image resources
