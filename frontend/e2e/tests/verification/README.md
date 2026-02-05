# Verification Queue E2E Tests

Comprehensive end-to-end tests for the verification queue using Playwright and the Page Object Model pattern.

## Test Coverage

### 1. Page Load and Initial State (4 tests)
- ✓ Load verification queue page
- ✓ Display pending count badge
- ✓ Show empty state when no items
- ✓ Display verification queue with items

### 2. Filtering (4 tests)
- ✓ Filter by status (pending/approved/rejected)
- ✓ Filter by confidence level (high/medium/low)
- ✓ Filter by entity type (tiger/facility)
- ✓ Combine multiple filters

### 3. Item Selection (3 tests)
- ✓ Select individual items with checkboxes
- ✓ Select all items with select-all checkbox
- ✓ Deselect all when clicking select-all again

### 4. Bulk Actions (3 tests)
- ✓ Bulk approve selected items with confirmation
- ✓ Bulk reject selected items with confirmation
- ✓ Cancel bulk actions when dialog is dismissed

### 5. Individual Item Actions (3 tests)
- ✓ Approve individual item
- ✓ Reject individual item
- ✓ Handle approve errors gracefully

### 6. Comparison Overlay (4 tests)
- ✓ Open comparison overlay when clicking view button
- ✓ Display query and match images in overlay
- ✓ Close comparison overlay when clicking close button
- ✓ Close overlay when pressing Escape key

### 7. Model Agreement Badge (3 tests)
- ✓ Display model agreement badge with correct text
- ✓ Show different badge styles for different agreement levels
- ✓ Show consensus indicator when all models agree

### 8. Pagination (5 tests)
- ✓ Navigate to next page
- ✓ Navigate to previous page
- ✓ Disable previous button on first page
- ✓ Disable next button on last page
- ✓ Display current page and total pages

### 9. Real-time Updates (1 test)
- ✓ Handle queue updates when items are reviewed

### 10. Accessibility (2 tests)
- ✓ Have proper ARIA labels
- ✓ Be keyboard navigable

## File Structure

```
frontend/e2e/
├── tests/
│   └── verification/
│       ├── verification.spec.ts    # Main test suite
│       └── README.md               # This file
├── pages/
│   └── verification/
│       ├── verification-queue.page.ts  # Page Object Model
│       └── index.ts
├── data/
│   └── factories/
│       ├── verification.factory.ts  # Test data factory
│       └── index.ts
└── helpers/
    └── auth.ts                      # Authentication helper
```

## Running Tests

### Run all verification tests
```bash
npm run test:e2e -- tests/verification/verification.spec.ts
```

### Run specific test suite
```bash
# Run only filtering tests
npm run test:e2e -- tests/verification/verification.spec.ts -g "Filtering"

# Run only bulk actions tests
npm run test:e2e -- tests/verification/verification.spec.ts -g "Bulk Actions"

# Run only pagination tests
npm run test:e2e -- tests/verification/verification.spec.ts -g "Pagination"
```

### Run in headed mode (visible browser)
```bash
npm run test:e2e -- tests/verification/verification.spec.ts --headed
```

### Run in debug mode
```bash
npm run test:e2e -- tests/verification/verification.spec.ts --debug
```

### Generate test report
```bash
npm run test:e2e -- tests/verification/verification.spec.ts --reporter=html
```

## Page Object Model

The tests use the `VerificationQueuePage` class which provides:

### Locators
- `pageTitle` - Page heading
- `pendingCount` - Pending items count badge
- `queueTable` - Main queue table
- `queueRows` - Individual queue rows
- `bulkActionsDropdown` - Bulk actions menu
- `comparisonOverlay` - Image comparison modal
- Filter locators (status, confidence, entity type)

### Actions
- `goto()` - Navigate to verification queue
- `approveItem(index)` - Approve item at index
- `rejectItem(index)` - Reject item at index
- `viewComparison(index)` - Open comparison for item
- `selectRow(index)` - Select checkbox for item
- `selectAllRows()` - Toggle select all
- `bulkApprove()` - Approve selected items
- `bulkReject()` - Reject selected items
- `filterByConfidence(level)` - Filter by confidence
- `filterByModel(model)` - Filter by model

### Assertions
- `expectQueueCount(count)` - Assert number of rows
- `expectEmptyState()` - Assert empty state visible
- `expectComparisonVisible()` - Assert overlay visible
- `expectModelAgreement(index, text)` - Assert badge text

## Test Data Factories

The `verification.factory.ts` file provides factory functions:

```typescript
// Create single items
createVerificationItem()           // Standard item
createHighConfidenceItem()         // High confidence (>90%)
createLowConfidenceItem()          // Low confidence (<70%)
createApprovedItem()               // Already approved
createRejectedItem()               // Already rejected
createFacilityVerificationItem()  // Facility entity type

// Create multiple items
createVerificationQueue(10)       // 10 diverse items
```

## API Mocking

Tests mock the following endpoints:

- `GET /api/verification/queue` - Get queue items
- `POST /api/verification/:id/approve` - Approve item
- `POST /api/verification/:id/reject` - Reject item
- `POST /api/verification/bulk-approve` - Bulk approve
- `POST /api/verification/bulk-reject` - Bulk reject

Mocking allows tests to run without a backend server and control exact data scenarios.

## Key Testing Patterns

### 1. Arrange-Act-Assert
```typescript
test('should approve individual item', async ({ page }) => {
  // Arrange - Set up mocks and test data
  const mockItems = createVerificationQueue(3)
  await page.route('**/api/verification/queue*', ...)

  // Act - Perform the action
  await verificationPage.goto()
  await verificationPage.approveItem(0)

  // Assert - Verify expected outcome
  expect(approvedItemId).toBe(mockItems[0].id)
  await verificationPage.expectToastWithText(/approved/i)
})
```

### 2. Route Mocking for Different Scenarios
```typescript
// Mock different responses based on query parameters
await page.route('**/api/verification/queue*', async (route) => {
  const url = new URL(route.request().url())
  const status = url.searchParams.get('status')

  // Return filtered data based on query
  const filteredItems = allItems.filter(item =>
    status ? item.status === status : true
  )

  await route.fulfill({ body: JSON.stringify({ items: filteredItems }) })
})
```

### 3. Dialog Handling
```typescript
// Accept confirmation dialog
page.on('dialog', async (dialog) => {
  expect(dialog.message()).toContain('approve')
  await dialog.accept()
})

// Dismiss confirmation dialog
page.on('dialog', async (dialog) => {
  await dialog.dismiss()
})
```

## Best Practices

1. **Use Page Object Model** - All page interactions through `VerificationQueuePage`
2. **Use data-testid selectors** - Stable, semantic selectors
3. **Mock API responses** - Deterministic tests, no backend dependency
4. **Wait for operations** - Use `waitForSpinnerToDisappear()` after actions
5. **Test user flows** - Test complete workflows, not just units
6. **Verify side effects** - Check API calls, UI updates, notifications
7. **Test error states** - Include error handling tests
8. **Accessibility testing** - Verify ARIA labels and keyboard navigation

## Troubleshooting

### Tests fail with "Element not found"
- Check that the component uses the expected `data-testid` attributes
- Verify the component is mounted before interacting
- Use `await expect(element).toBeVisible()` before interactions

### Tests timeout
- Increase timeout in `playwright.config.ts`
- Check for uncaught promises or loading states
- Verify API routes are mocked correctly

### Flaky tests
- Add explicit waits (`waitForSpinnerToDisappear()`)
- Use `toBeVisible()` assertions before interactions
- Check for race conditions in async operations

### Mock not intercepting requests
- Verify route pattern matches actual request URL
- Check timing - set up routes before navigation
- Use `page.route()` instead of `context.route()` for test-specific mocks

## Contributing

When adding new verification features:

1. Add corresponding locator to `VerificationQueuePage`
2. Add action method if needed
3. Create test data factory function if needed
4. Write test(s) following existing patterns
5. Update this README with new test coverage

## Related Documentation

- [Playwright Documentation](https://playwright.dev/)
- [Page Object Model Pattern](https://playwright.dev/docs/pom)
- [Test Fixtures](https://playwright.dev/docs/test-fixtures)
- [API Mocking](https://playwright.dev/docs/mock)
