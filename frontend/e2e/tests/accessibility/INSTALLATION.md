# Installing @axe-core/playwright for Accessibility Testing

## Quick Installation

Run the following command from the `frontend` directory:

```bash
npm install --save-dev @axe-core/playwright
```

## Verification

Verify the installation:

```bash
npm list @axe-core/playwright
```

Expected output:
```
tiger-id-frontend@1.0.0 C:\Users\noah\Desktop\Tiger ID\frontend
└── @axe-core/playwright@4.x.x
```

## Running the Tests

After installation, run the accessibility tests:

```bash
# Run all accessibility tests
npm run test:e2e:accessibility

# Or use Playwright directly
npx playwright test accessibility

# Run in UI mode for interactive debugging
npx playwright test accessibility --ui

# Run with headed browser to see what's happening
npx playwright test accessibility --headed

# Run specific test
npx playwright test accessibility.spec.ts -g "Login page"
```

## Package Information

- **Package**: `@axe-core/playwright`
- **Repository**: https://github.com/dequelabs/axe-core-npm
- **Documentation**: https://github.com/dequelabs/axe-core-npm/tree/develop/packages/playwright
- **License**: MPL-2.0

## What Gets Installed

The package includes:
- axe-core: The accessibility testing engine
- Playwright integration: Seamless integration with Playwright tests
- Rule sets: WCAG 2.0/2.1 Level A and AA rules
- Reporting: Detailed violation reports with remediation guidance

## Dependencies

The package requires:
- Playwright (already installed in this project)
- Node.js 18+ (already satisfied)

## Troubleshooting

### Module not found error
If you see `Cannot find module '@axe-core/playwright'`:

1. Ensure you're in the `frontend` directory
2. Run `npm install --save-dev @axe-core/playwright`
3. Verify installation with `npm list @axe-core/playwright`

### TypeScript errors
If you see TypeScript errors about missing types:

```bash
npm install --save-dev @types/node
```

### Version conflicts
If you encounter version conflicts, check your package.json:

```json
{
  "devDependencies": {
    "@axe-core/playwright": "^4.10.2",
    "@playwright/test": "^1.47.2"
  }
}
```

Both packages should be compatible. If not, update Playwright:

```bash
npm install --save-dev @playwright/test@latest
```

## CI/CD Integration

For GitHub Actions, add to your workflow:

```yaml
- name: Install dependencies
  run: npm ci

- name: Install Playwright browsers
  run: npx playwright install --with-deps

- name: Run accessibility tests
  run: npm run test:e2e:accessibility
```

## Next Steps

After installation:

1. Read `README.md` in this directory for test documentation
2. Run the tests: `npm run test:e2e:accessibility`
3. Review the test results and fix any violations
4. Integrate into your CI/CD pipeline

## Additional Resources

- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [Deque University](https://dequeuniversity.com/rules/axe/4.4/)
- [Playwright Accessibility Testing Guide](https://playwright.dev/docs/accessibility-testing)
