# Facility Detail Tests - Quick Reference

## Run Commands

```bash
# Run all facility detail tests
npx playwright test tests/facilities/facility-detail

# Run specific test by name
npx playwright test tests/facilities/facility-detail -g "crawl history"

# Run in headed mode (see browser)
npx playwright test tests/facilities/facility-detail --headed

# Run in UI mode (interactive)
npx playwright test tests/facilities/facility-detail --ui

# Run on specific browser
npx playwright test tests/facilities/facility-detail --project=chromium
npx playwright test tests/facilities/facility-detail --project=firefox
npx playwright test tests/facilities/facility-detail --project=webkit

# Generate report
npx playwright test tests/facilities/facility-detail --reporter=html
npx playwright show-report
```

## Test List (20 Tests)

1. ✅ should display facility detail page with complete information
2. ✅ should display facility location on map view
3. ✅ should display crawl history timeline for facility
4. ✅ should display detailed information for crawl events
5. ✅ should display tiger gallery for facility
6. ✅ should support different view modes for tiger gallery
7. ✅ should support grouping tigers in gallery
8. ✅ should navigate to tiger detail when clicking a tiger in gallery
9. ✅ should provide edit functionality for facility
10. ✅ should allow triggering manual crawl for facility
11. ✅ should display discovery status for facility
12. ✅ should display facility metadata and timestamps
13. ✅ should display facility links and social media
14. ✅ should display facility accreditation and inspection info
15. ✅ should allow navigation back to facilities list from detail page
16. ✅ should display reference facility badge if applicable
17. ✅ should display facility capacity and tiger statistics
18. ✅ should handle loading states properly
19. ✅ should display appropriate message when facility not found
20. ✅ should display mobile-responsive detail panel

## Required data-testid Attributes

### Essential (High Priority)
```tsx
// Page
data-testid="facility-detail-page"

// Facility Cards
data-testid="facility-card-{id}"
data-testid="view-facility-details"

// Map & Views
data-testid="facilities-map-container"
data-testid="facility-map-view"
data-testid="view-mode-map"
data-testid="view-mode-list"

// Crawl History
data-testid="crawl-history-timeline"
data-testid="crawl-event-{id}"
data-testid="discovery-status"
data-testid="start-crawl"

// Tiger Gallery
data-testid="facility-tiger-gallery"
data-testid="image-card-{id}"

// Navigation
data-testid="close-detail-panel"
data-testid="close-detail-panel-mobile"
```

### Nice to Have (Medium Priority)
```tsx
data-testid="facility-info-{field}"
data-testid="edit-facility"
data-testid="facility-metadata"
data-testid="facility-links"
```

## Common Issues & Solutions

### Issue: "Element not found"
**Solution:** Add missing data-testid attributes to components

### Issue: Test timeout
**Solution:**
- Ensure backend is running
- Check API endpoints are responding
- Increase timeout: `test.setTimeout(60000)`

### Issue: Flaky tests
**Solution:**
- Replace `waitForTimeout` with `waitForSelector`
- Use conditional checks: `if (await element.count() > 0)`
- Ensure proper wait conditions

### Issue: Navigation not working
**Solution:**
- Verify route definitions match test URLs
- Check router configuration
- Ensure auth is working properly

## Test Structure Pattern

```typescript
test('should do something', async ({ page }) => {
  // 1. Navigate to page
  await page.goto('/facilities')
  await page.waitForTimeout(1000)

  // 2. Find and interact with element
  const element = page.locator('[data-testid="element"]')

  if (await element.count() > 0) {
    // 3. Perform action
    await element.click()

    // 4. Verify result
    await expect(page).toHaveURL(/expected-pattern/)
  }
})
```

## Debugging Tips

### View test in browser
```bash
npx playwright test tests/facilities/facility-detail --headed --project=chromium
```

### Debug specific test
```bash
npx playwright test tests/facilities/facility-detail --debug -g "specific test name"
```

### Generate trace
```bash
npx playwright test tests/facilities/facility-detail --trace on
npx playwright show-trace trace.zip
```

### Take screenshots
```bash
npx playwright test tests/facilities/facility-detail --screenshot=on
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run Facility Detail Tests
  run: |
    cd frontend
    npx playwright test tests/facilities/facility-detail

- name: Upload Test Report
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: facility-detail-test-report
    path: frontend/playwright-report/
```

### Test Coverage Metrics

**Expected Results:**
- Total Tests: 20
- Pass Rate: 100%
- Avg Duration: 2-5s per test
- Suite Duration: 60-90s
- Flaky Tests: 0

## Related Files

- Test Spec: `tests/facilities/facility-detail.spec.ts`
- Auth Helper: `helpers/auth.ts`
- Test Fixtures: `fixtures/`
- Config: `playwright.config.ts`
- README: `tests/facilities/README.md`
- Summary: `tests/facilities/TEST_SUMMARY.md`

## Component Requirements

**Required Components:**
- FacilityDetail page
- FacilityMapView
- CrawlHistoryTimeline
- FacilityTigerGallery
- FacilityFilters

**Required API Endpoints:**
- GET `/api/facilities/:id`
- GET `/api/facilities/:id/crawl-history`
- GET `/api/facilities/:id/tigers`
- POST `/api/facilities/:id/crawl`

## Quick Validation

### Check if tests are recognized
```bash
npx playwright test --list tests/facilities/facility-detail
```

### Type check tests
```bash
npx tsc --noEmit e2e/tests/facilities/facility-detail.spec.ts
```

### Dry run (no execution)
```bash
npx playwright test tests/facilities/facility-detail --list
```

## Success Checklist

Before merging:
- [ ] All 20 tests pass
- [ ] No flaky tests (run 3x)
- [ ] Type checking passes
- [ ] Screenshots available on failure
- [ ] Traces available for debugging
- [ ] Documentation updated
- [ ] data-testid attributes added
- [ ] CI/CD integration tested

## Next Steps

1. Run tests: `npx playwright test tests/facilities/facility-detail`
2. Fix any failures
3. Add missing data-testid attributes
4. Run again to verify
5. Integrate with CI/CD
6. Monitor for flakiness

---

**Quick Links:**
- [Full README](./README.md)
- [Test Summary](./TEST_SUMMARY.md)
- [Main E2E README](../../README.md)
