# Refactored Components Test Guide

## Quick Start

Run all refactored component tests:
```bash
cd frontend
node test-refactored-components.js
```

## What Was Tested

### 1. API Module Split (api.test.ts)
**Location:** `src/app/__tests__/api.test.ts`

Verifies the API split into domain modules works correctly.

**Key Tests:**
- ✓ baseApi exports with correct reducer path
- ✓ All Investigation 2.0 endpoints present
- ✓ Tiger identification endpoints available
- ✓ Discovery, Verification, Analytics endpoints working
- ✓ Hooks exported and follow naming conventions
- ✓ Backward compatibility maintained

**Run:** `npm run test -- src/app/__tests__/api.test.ts`

### 2. Auth RTK Query Migration (authSlice.rtk.test.ts)
**Location:** `src/features/auth/__tests__/authSlice.rtk.test.ts`

Verifies auth migrated to RTK Query successfully.

**Key Tests:**
- ✓ RTK Query mutations integrate with auth slice
- ✓ State updates from API responses work
- ✓ User authentication state tracked correctly
- ✓ Token storage works

**Run:** `npm run test -- src/features/auth/__tests__/authSlice.rtk.test.ts`

### 3. Investigation2Context (Investigation2Context.test.tsx)
**Location:** `src/context/__tests__/Investigation2Context.test.tsx`

Verifies Investigation2 uses Context instead of prop drilling.

**Key Tests:**
- ✓ Provider supplies all 19 context properties
- ✓ useInvestigation2 hook throws error outside provider
- ✓ State management functions present
- ✓ WebSocket integration properties exist
- ✓ Progress tracking works

**Run:** `npm run test -- src/context/__tests__/Investigation2Context.test.tsx`

### 4. Type Safety (investigation2.test.ts)
**Location:** `src/types/__tests__/investigation2.test.ts`

Ensures no `any` types were used in refactoring.

**Key Tests:**
- ✓ TigerMatch type properly typed (not any)
- ✓ VerifiedCandidate extends TigerMatch
- ✓ Investigation2Response properly typed
- ✓ All types explicitly reject `any`
- ✓ Optional fields typed as `| undefined`

**Run:** `npm run test -- src/types/__tests__/investigation2.test.ts`

### 5. Component Props (Investigation2ResultsEnhanced.test.tsx)
**Location:** `src/components/investigations/__tests__/Investigation2ResultsEnhanced.test.tsx`

Verifies Investigation2ResultsEnhanced receives typed props.

**Key Tests:**
- ✓ Component receives Investigation2Response (not any)
- ✓ TigerMatch types used correctly
- ✓ Enhanced workflow data typed
- ✓ Report audience uses enum
- ✓ Callbacks properly typed

**Run:** `npm run test -- src/components/investigations/__tests__/Investigation2ResultsEnhanced.test.tsx`

## TypeScript Check

Verify no type errors exist:
```bash
npx tsc --noEmit
```

This must pass with 0 errors.

## Test Statistics

- **Test Files:** 5
- **Test Cases:** 46
- **Lines of Code:** 814
- **Coverage:** API, Auth, Context, Types, Components

## Regression Prevention

These tests will fail if:

1. ❌ API endpoints are removed/renamed
2. ❌ Auth state structure changes
3. ❌ Investigation2Context properties removed
4. ❌ Any type used instead of proper types
5. ❌ Component props revert to `any`
6. ❌ Hooks renamed incorrectly
7. ❌ Context used without provider

## Common Issues

### Issue: Tests fail with import errors
**Solution:** Ensure all dependencies installed: `npm install`

### Issue: TypeScript errors
**Solution:** Check for `any` types and add proper type annotations

### Issue: Context tests fail
**Solution:** Verify Investigation2Provider wraps test components

### Issue: API tests fail
**Solution:** Check api.ts exports all hooks and endpoints

## Integration with CI/CD

Add to your CI pipeline:
```yaml
- name: Test Refactored Components
  run: |
    cd frontend
    node test-refactored-components.js
```

## When to Run

Run these tests:
- ✅ Before committing refactored code
- ✅ Before creating pull requests
- ✅ After modifying API endpoints
- ✅ After changing types
- ✅ After updating Investigation2 components
- ✅ In CI/CD pipeline

## Files Reference

### Test Files
```
src/app/__tests__/api.test.ts
src/features/auth/__tests__/authSlice.rtk.test.ts
src/context/__tests__/Investigation2Context.test.tsx
src/types/__tests__/investigation2.test.ts
src/components/investigations/__tests__/Investigation2ResultsEnhanced.test.tsx
```

### Documentation
```
REFACTORED_COMPONENT_TESTS.md (this file)
test-refactored-components.js (test runner)
```

## Success Criteria

All tests passing means:
- ✅ API properly organized into domain modules
- ✅ Auth successfully migrated to RTK Query
- ✅ Investigation2 uses Context (no prop drilling)
- ✅ No `any` types in refactored code
- ✅ Component props properly typed

## Next Steps

1. Run tests: `node test-refactored-components.js`
2. Fix any failures
3. Commit test files
4. Add to CI/CD pipeline
5. Document in main README

## Support

For issues:
1. Check TypeScript errors first
2. Verify all imports are correct
3. Ensure providers wrap components in tests
4. Check that types match actual implementations
5. Review test documentation in REFACTORED_COMPONENT_TESTS.md
