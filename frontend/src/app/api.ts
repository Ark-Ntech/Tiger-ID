/**
 * API Module - Backward Compatibility Re-exports
 *
 * This file maintains backward compatibility with existing imports.
 * All API functionality is now organized in the api/ directory:
 *
 *   frontend/src/app/api/
 *   ├── index.ts           # Re-exports all APIs and hooks
 *   ├── baseApi.ts         # Base RTK Query configuration
 *   ├── authApi.ts         # Auth and user endpoints
 *   ├── investigationApi.ts # Investigation endpoints
 *   ├── tigerApi.ts        # Tiger endpoints
 *   ├── facilityApi.ts     # Facility endpoints
 *   ├── verificationApi.ts # Verification endpoints
 *   ├── discoveryApi.ts    # Discovery endpoints
 *   └── analyticsApi.ts    # Analytics and integrations
 *
 * For new code, prefer importing from specific modules:
 *   import { useGetTigersQuery } from '@/app/api/tigerApi'
 *
 * Or from the index for convenience:
 *   import { useGetTigersQuery, api } from '@/app/api'
 */

// Re-export everything from the api module
export * from './api/index'

// Also export the api directly for store configuration
export { baseApi as api } from './api/baseApi'
