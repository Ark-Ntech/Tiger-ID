import { useState } from 'react'
import Card from '../components/common/Card'
import WebSearchTab from '../components/investigations/WebSearchTab'
import ReverseImageSearchTab from '../components/investigations/ReverseImageSearchTab'
import NewsMonitorTab from '../components/investigations/NewsMonitorTab'
import LeadGenerationTab from '../components/investigations/LeadGenerationTab'
import RelationshipAnalysisTab from '../components/investigations/RelationshipAnalysisTab'
import NetworkGraphTab from '../components/investigations/NetworkGraphTab'
import EvidenceCompilationTab from '../components/investigations/EvidenceCompilationTab'
import CrawlSchedulerTab from '../components/investigations/CrawlSchedulerTab'
import ReferenceDataTab from '../components/investigations/ReferenceDataTab'
import {
  GlobeAltIcon,
  PhotoIcon,
  NewspaperIcon,
  LightBulbIcon,
  ShareIcon,
  CubeIcon,
  DocumentTextIcon,
  ServerIcon,
  DocumentArrowUpIcon,
} from '@heroicons/react/24/outline'

// All tab components are now imported above

const InvestigationTools = () => {
  const [activeTab, setActiveTab] = useState(0)

  const tabs = [
    { name: 'Web Search', icon: GlobeAltIcon, component: WebSearchTab },
    { name: 'Reverse Image Search', icon: PhotoIcon, component: ReverseImageSearchTab },
    { name: 'News Monitor', icon: NewspaperIcon, component: NewsMonitorTab },
    { name: 'Lead Generation', icon: LightBulbIcon, component: LeadGenerationTab },
    { name: 'Relationship Analysis', icon: ShareIcon, component: RelationshipAnalysisTab },
    { name: 'Network Graph', icon: CubeIcon, component: NetworkGraphTab },
    { name: 'Evidence Compilation', icon: DocumentTextIcon, component: EvidenceCompilationTab },
    { name: 'Crawl Scheduler', icon: ServerIcon, component: CrawlSchedulerTab },
    { name: 'Reference Data', icon: DocumentArrowUpIcon, component: ReferenceDataTab },
  ]

  const ActiveComponent = tabs[activeTab].component

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">🔎 Investigation Tools</h1>
        <p className="text-gray-600 mt-2">Advanced tools for web intelligence, lead generation, and analysis</p>
      </div>

      {/* Tab Navigation */}
      <Card padding="none">
        <div className="border-b border-gray-200">
          <nav className="flex overflow-x-auto -mb-px" aria-label="Tabs">
            {tabs.map((tab, index) => {
              const Icon = tab.icon
              return (
                <button
                  key={index}
                  onClick={() => setActiveTab(index)}
                  className={`
                    flex items-center gap-2 whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm
                    transition-colors
                    ${
                      activeTab === index
                        ? 'border-primary-600 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  <Icon className="h-5 w-5" />
                  {tab.name}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          <ActiveComponent />
        </div>
      </Card>
    </div>
  )
}

export default InvestigationTools
