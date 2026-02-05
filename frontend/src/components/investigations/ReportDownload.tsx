import React, { useState } from 'react';
import {
  DocumentArrowDownIcon,
  DocumentTextIcon,
  CodeBracketIcon,
  EyeIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import type { ReportAudience } from '../../types/investigation2';

interface ReportDownloadProps {
  investigationId: string;
  audience: ReportAudience;
  onDownload?: (format: string) => void;
  disabled?: boolean;
}

type ExportFormat = 'markdown' | 'pdf' | 'json';

interface IncludeOptions {
  evidence: boolean;
  methodology: boolean;
  technicalDetails: boolean;
  rawEmbeddings: boolean;
}

const AUDIENCE_LABELS: Record<ReportAudience, string> = {
  law_enforcement: 'Law Enforcement',
  conservation: 'Conservation',
  internal: 'Internal/Technical',
  public: 'Public'
};

const FORMAT_INFO: Record<ExportFormat, { label: string; icon: React.ElementType; description: string }> = {
  markdown: {
    label: 'Markdown',
    icon: DocumentTextIcon,
    description: 'Plain text with formatting, ideal for documentation'
  },
  pdf: {
    label: 'PDF',
    icon: DocumentArrowDownIcon,
    description: 'Professional formatted document for sharing'
  },
  json: {
    label: 'JSON',
    icon: CodeBracketIcon,
    description: 'Machine-readable format with all data'
  }
};

export const ReportDownload: React.FC<ReportDownloadProps> = ({
  investigationId,
  audience,
  onDownload,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('pdf');
  const [includeOptions, setIncludeOptions] = useState<IncludeOptions>({
    evidence: true,
    methodology: true,
    technicalDetails: false,
    rawEmbeddings: false
  });
  const [isDownloading, setIsDownloading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const handleDownload = async () => {
    setIsDownloading(true);

    try {
      const params = new URLSearchParams({
        include_evidence: includeOptions.evidence.toString(),
        include_steps: includeOptions.methodology.toString(),
        audience: audience
      });

      if (includeOptions.technicalDetails) {
        params.append('include_metadata', 'true');
      }

      const baseUrl = import.meta.env.PROD
        ? (import.meta.env.VITE_API_URL || 'http://localhost:8000')
        : '';

      const response = await fetch(
        `${baseUrl}/api/v1/investigations/${investigationId}/export/${selectedFormat}?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );

      if (!response.ok) {
        throw new Error('Download failed');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      const extension = selectedFormat === 'markdown' ? 'md' : selectedFormat;
      a.download = `investigation-${investigationId}-${audience}.${extension}`;

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      onDownload?.(selectedFormat);
      setIsOpen(false);
    } catch (error) {
      console.error('Download failed:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  const toggleOption = (key: keyof IncludeOptions) => {
    setIncludeOptions(prev => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(true)}
        disabled={disabled}
        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <DocumentArrowDownIcon className="w-5 h-5" />
        Download Report
      </button>

      {/* Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Download Investigation Report</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded hover:bg-gray-100 transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Content */}
            <div className="px-6 py-4 space-y-6">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Format</label>
                <div className="grid grid-cols-3 gap-3">
                  {(Object.keys(FORMAT_INFO) as ExportFormat[]).map((format) => {
                    const info = FORMAT_INFO[format];
                    const Icon = info.icon;
                    const isSelected = selectedFormat === format;

                    return (
                      <button
                        key={format}
                        onClick={() => setSelectedFormat(format)}
                        className={`flex flex-col items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                          isSelected
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <Icon className={`w-6 h-6 ${isSelected ? 'text-blue-600' : 'text-gray-400'}`} />
                        <span className={`text-sm font-medium ${isSelected ? 'text-blue-700' : 'text-gray-600'}`}>
                          {info.label}
                        </span>
                      </button>
                    );
                  })}
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  {FORMAT_INFO[selectedFormat].description}
                </p>
              </div>

              {/* Audience Display */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Audience</label>
                <div className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg">
                  <span className="text-sm text-gray-900 font-medium">
                    {AUDIENCE_LABELS[audience]}
                  </span>
                  <span className="text-xs text-gray-500">
                    (change in results page)
                  </span>
                </div>
              </div>

              {/* Include Options */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">Include</label>
                <div className="space-y-2">
                  {[
                    { key: 'evidence' as const, label: 'Evidence citations' },
                    { key: 'methodology' as const, label: 'Methodology steps' },
                    { key: 'technicalDetails' as const, label: 'Technical debug info' },
                    { key: 'rawEmbeddings' as const, label: 'Raw embeddings data' }
                  ].map(({ key, label }) => (
                    <label key={key} className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={includeOptions[key]}
                        onChange={() => toggleOption(key)}
                        className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                      <span className="text-sm text-gray-700">{label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
              <button
                onClick={() => setShowPreview(true)}
                className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
              >
                <EyeIcon className="w-4 h-4" />
                Preview
              </button>
              <button
                onClick={handleDownload}
                disabled={isDownloading}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
              >
                {isDownloading ? (
                  <>
                    <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Downloading...
                  </>
                ) : (
                  <>
                    <DocumentArrowDownIcon className="w-4 h-4" />
                    Download Report
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {showPreview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl mx-4 max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Report Preview</h3>
              <button
                onClick={() => setShowPreview(false)}
                className="p-1 rounded hover:bg-gray-100 transition-colors"
              >
                <XMarkIcon className="w-5 h-5 text-gray-500" />
              </button>
            </div>
            <div className="flex-1 overflow-auto p-6">
              <div className="prose max-w-none">
                <p className="text-gray-500 text-center py-12">
                  Preview loading for {AUDIENCE_LABELS[audience]} report...
                </p>
              </div>
            </div>
            <div className="flex items-center justify-end px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-xl">
              <button
                onClick={() => setShowPreview(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ReportDownload;
