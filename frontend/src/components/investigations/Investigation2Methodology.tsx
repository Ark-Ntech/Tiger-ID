import React from 'react';

interface ReasoningStep {
  step: number;
  phase: string;
  action: string;
  reasoning: string;
  evidence: string[];
  conclusion: string;
  confidence: number;
}

interface Investigation2MethodologyProps {
  steps: ReasoningStep[];
}

export const Investigation2Methodology: React.FC<Investigation2MethodologyProps> = ({ steps }) => {
  if (!steps || steps.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>No methodology data available</p>
      </div>
    );
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'bg-green-500';
    if (confidence >= 60) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  return (
    <div className="methodology-timeline p-4">
      <div className="mb-6">
        <h3 className="text-2xl font-bold text-gray-800">Investigation Methodology</h3>
        <p className="text-gray-600 mt-1">
          Step-by-step reasoning chain showing how conclusions were reached
        </p>
      </div>

      {steps.map((step, idx) => (
        <div key={idx} className="reasoning-step mb-6 relative">
          {/* Timeline connector */}
          {idx < steps.length - 1 && (
            <div className="absolute left-6 top-12 h-full w-0.5 bg-gray-300 z-0" />
          )}

          {/* Step content */}
          <div className="relative z-10">
            {/* Step header */}
            <div className="flex items-center gap-4 mb-2">
              <div
                className={`w-12 h-12 rounded-full ${getConfidenceColor(step.confidence)} text-white flex items-center justify-center font-bold shadow-md flex-shrink-0`}
              >
                {step.step}
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-lg text-gray-800">{step.phase}</h4>
                <span className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded">
                  {step.confidence}% confidence
                </span>
              </div>
            </div>

            {/* Step details */}
            <div className="ml-16 bg-gray-50 rounded-lg p-4 shadow-sm border border-gray-200">
              {/* Action */}
              <div className="mb-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-gray-700">Action:</span>
                </div>
                <p className="text-sm text-gray-600">{step.action}</p>
              </div>

              {/* Reasoning - highlighted box */}
              <div className="mb-3 bg-white rounded p-3 border-l-4 border-blue-500 shadow-sm">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-gray-700">Reasoning:</span>
                  <span className="text-xs text-blue-600 font-medium">Thinking Tokens</span>
                </div>
                <p className="text-sm italic text-gray-700 leading-relaxed">
                  {step.reasoning}
                </p>
              </div>

              {/* Evidence */}
              <div className="mb-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-gray-700">Evidence:</span>
                </div>
                <ul className="list-disc ml-5 space-y-1">
                  {step.evidence.map((ev, i) => (
                    <li key={i} className="text-sm text-gray-600">
                      {ev}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Conclusion */}
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-semibold text-sm text-gray-700">Conclusion:</span>
                </div>
                <p className="text-sm text-gray-600 font-medium">{step.conclusion}</p>
              </div>
            </div>
          </div>
        </div>
      ))}

      {/* Summary footer */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2">Methodology Summary</h4>
        <p className="text-sm text-blue-800">
          This investigation followed a {steps.length}-step process to analyze the tiger image and generate
          conclusions. Each step builds on previous findings to ensure transparent, evidence-based results.
        </p>
      </div>
    </div>
  );
};
