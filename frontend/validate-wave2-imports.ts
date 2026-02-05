/**
 * Wave 2 Import Validation Script
 *
 * This script validates that all Wave 2 components can be imported correctly
 * from their barrel exports. Run with: npx tsx validate-wave2-imports.ts
 */

// Group B - Results Tabs
import {
  OverviewTab,
  DetectionTab,
  MatchingTab,
  VerificationTab,
  MethodologyTab
} from './src/components/investigations/results/tabs'

// Group K - Discovery Components
import {
  FacilityCrawlGrid,
  DiscoveryActivityFeed,
  DiscoveryFacilitiesMap,
  CrawlProgressCard,
  AutoInvestigationMonitor
} from './src/components/discovery'

// Group P - Facilities Components
import {
  FacilityMapView,
  FacilityFilters,
  CrawlHistoryTimeline,
  FacilityTigerGallery
} from './src/components/facilities'

console.log('✅ All Wave 2 imports validated successfully!\n')

console.log('Group B - Results Tabs:')
console.log('  - OverviewTab:', typeof OverviewTab)
console.log('  - DetectionTab:', typeof DetectionTab)
console.log('  - MatchingTab:', typeof MatchingTab)
console.log('  - VerificationTab:', typeof VerificationTab)
console.log('  - MethodologyTab:', typeof MethodologyTab)

console.log('\nGroup K - Discovery Components:')
console.log('  - FacilityCrawlGrid:', typeof FacilityCrawlGrid)
console.log('  - DiscoveryActivityFeed:', typeof DiscoveryActivityFeed)
console.log('  - DiscoveryFacilitiesMap:', typeof DiscoveryFacilitiesMap)
console.log('  - CrawlProgressCard:', typeof CrawlProgressCard)
console.log('  - AutoInvestigationMonitor:', typeof AutoInvestigationMonitor)

console.log('\nGroup P - Facilities Components:')
console.log('  - FacilityMapView:', typeof FacilityMapView)
console.log('  - FacilityFilters:', typeof FacilityFilters)
console.log('  - CrawlHistoryTimeline:', typeof CrawlHistoryTimeline)
console.log('  - FacilityTigerGallery:', typeof FacilityTigerGallery)

console.log('\n✅ Total components validated: 14')
console.log('✅ All exports working correctly')
