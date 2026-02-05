# Refactored Component Tests

This document describes the comprehensive test suite for the frontend refactoring work.

## Test Coverage

### 1. API Module Tests (`src/app/__tests__/api.test.ts`)

Tests verify the API split and domain module organization:

**Tested:**
- baseApi exports correctly with proper reducer path
- All domain endpoints are available (Investigation, Tiger, Facility, etc.)
- Investigation 2.0 endpoints are properly typed
- Hooks follow naming conventions
- Backward compatibility maintained

**Prevents Regression:**
- Missing endpoints after API reorganization
- Incorrect hook naming patterns
- Breaking changes to existing API consumers

### 2. Auth RTK Query Tests (`src/features/auth/__tests__/authSlice.rtk.test.ts`)

Tests verify the auth migration to RTK Query:

**Tested:**
- RTK Query mutations integrate with auth slice
- State updates from RTK Query responses work correctly
- Auth actions (login, logout, register) function properly
- Token storage and retrieval

**Prevents Regression:**
- Auth state corruption after RTK Query migration
- Missing auth action handlers
- Token management issues

### 3. Investigation2Context Tests (`src/context/__tests__/Investigation2Context.test.tsx`)

Tests verify the Investigation2 Context implementation:

**Tested:**
- Context provides all required values
- useInvestigation2 hook throws error outside provider
- All context properties are properly typed
- State management functions work correctly
- WebSocket integration properties exist

**Prevents Regression:**
- Missing context properties
- Prop drilling reintroduction
- Context usage without provider
- Type safety violations

### 4. Type Safety Tests (`src/types/__tests__/investigation2.test.ts`)

Tests that would fail if any types are reintroduced:

**Tested:**
- TigerMatch type has proper string/number fields
- VerifiedCandidate extends TigerMatch correctly
- Investigation2Response type is properly typed
- All types explicitly reject `any`
- Optional fields are properly typed as `| undefined`

**Prevents Regression:**
- `any` type reintroduction
- Missing required fields
- Incorrect optional field typing
- Type safety violations

### 5. Component Props Tests (`src/components/investigations/__tests__/Investigation2ResultsEnhanced.test.tsx`)

Tests verify Investigation2ResultsEnhanced receives typed props:

**Tested:**
- Component receives Investigation2Response type (not any)
- TigerMatch types are properly used
- Enhanced workflow data (ImageQuality, VerifiedCandidate) is typed
- Report audience selection uses ReportAudience enum
- Callback functions have proper type signatures

**Prevents Regression:**
- Props reverting to `any` type
- Missing type annotations
- Incorrect match data types
- Type safety violations in component props

## Running Tests

### Run All Refactored Component Tests
```bash
npm run test -- src/app/__tests__/ src/features/auth/__tests__/authSlice.rtk.test.ts src/context/__tests__/ src/types/__tests__/ src/components/investigations/__tests__/Investigation2ResultsEnhanced.test.tsx
```

### Run Individual Test Suites
```bash
# API module tests
npm run test -- src/app/__tests__/api.test.ts

# Auth RTK Query tests
npm run test -- src/features/auth/__tests__/authSlice.rtk.test.ts

# Investigation2Context tests
npm run test -- src/context/__tests__/Investigation2Context.test.tsx

# Type safety tests
npm run test -- src/types/__tests__/investigation2.test.ts

# Component props tests
npm run test -- src/components/investigations/__tests__/Investigation2ResultsEnhanced.test.tsx
```

### Run TypeScript Type Check
```bash
npx tsc --noEmit
```

This verifies no type errors exist across the entire frontend codebase.

### Run All Tests with Script
```bash
node test-refactored-components.js
```

This script runs all refactored component tests and TypeScript checks in sequence.

## Test Philosophy

### Type Safety
All tests verify that types are explicit and not `any`. Tests use `expectTypeOf().not.toBeAny()` to fail if any types are reintroduced.

### Integration Testing
Tests verify that refactored components integrate correctly with:
- RTK Query hooks
- Redux store
- Context providers
- React component hierarchy

### Backward Compatibility
Tests ensure refactored code maintains backward compatibility:
- Original API exports still work
- Hook naming conventions unchanged
- Component interfaces preserved

## Key Test Patterns

### Type Safety Testing
```typescript
it('should not allow any type', () => {
  expectTypeOf<TigerMatch>().not.toBeAny()
})
```

### Context Testing
```typescript
it('should throw error when used outside provider', () => {
  expect(() => {
    renderHook(() => useInvestigation2())
  }).toThrow('must be used within Investigation2Provider')
})
```

### RTK Query Integration Testing
```typescript
it('should update state from RTK Query login response', () => {
  store.dispatch(setUser(mockUser))
  const state = store.getState().auth
  expect(state.user).toEqual(mockUser)
})
```

### Component Props Type Testing
```typescript
it('should receive properly typed investigation prop', () => {
  render(
    <Investigation2ResultsEnhanced
      investigation={mockInvestigation}
    />
  )
  expect(mockInvestigation.investigation_id).toBe('inv-123')
})
```

## Expected Results

All tests should pass, and TypeScript check should report 0 errors:

```
✓ API Module Tests passed
✓ Auth RTK Query Tests passed
✓ Investigation2Context Tests passed
✓ Type Safety Tests passed
✓ Investigation2ResultsEnhanced Tests passed
✓ TypeScript check passed

✓ All refactored component tests passed!
```

## Continuous Integration

These tests should be run:
1. Before committing refactored code
2. In CI/CD pipeline before merging
3. After any changes to API, auth, or Investigation2 components
4. Whenever types are modified

## Troubleshooting

### TypeScript Errors
If `npx tsc --noEmit` fails:
1. Check for any `any` types in modified files
2. Verify all imports have proper type definitions
3. Check that Investigation2Response is properly typed
4. Ensure all component props have type annotations

### Test Failures
If tests fail:
1. Verify all dependencies are installed (`npm install`)
2. Check that API endpoints haven't changed
3. Ensure context providers are properly configured
4. Verify mock data matches expected types

### Import Errors
If tests show import errors:
1. Check that all modules export expected functions/types
2. Verify context files export both provider and hook
3. Ensure API file exports all hooks
4. Check that types are exported from investigation2.ts
