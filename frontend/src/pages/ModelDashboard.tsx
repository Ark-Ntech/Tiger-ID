import { useState, useEffect } from 'react'
import { useGetModelsAvailableQuery, useBenchmarkModelMutation } from '../app/api'
import Card from '../components/common/Card'
import Button from '../components/common/Button'
import LoadingSpinner from '../components/common/LoadingSpinner'
import Alert from '../components/common/Alert'
import Badge from '../components/common/Badge'
import { ChartBarIcon, ClockIcon, CpuChipIcon } from '@heroicons/react/24/outline'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const ModelDashboard = () => {
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [benchmarkResults, setBenchmarkResults] = useState<any>(null)
  const [isBenchmarking, setIsBenchmarking] = useState(false)

  const { data: modelsData, isLoading: modelsLoading } = useGetModelsAvailableQuery()
  const [_benchmarkModel, { isLoading: benchmarkLoading }] = useBenchmarkModelMutation()
  void _benchmarkModel // Reserved for benchmark feature

  const availableModels = modelsData?.data?.models || {}
  const modelNames = Object.keys(availableModels)

  // Mock performance data for visualization
  const [performanceData, setPerformanceData] = useState<any[]>([])

  useEffect(() => {
    // Generate mock performance data
    const mockData = modelNames.map((modelName) => ({
      model: modelName,
      rank1_accuracy: Math.random() * 0.3 + 0.7, // 70-100%
      map: Math.random() * 0.2 + 0.8, // 80-100%
      latency_ms: Math.random() * 200 + 100, // 100-300ms
      throughput: Math.random() * 5 + 5, // 5-10 img/s
    }))
    setPerformanceData(mockData)
  }, [modelNames])

  const handleBenchmark = async () => {
    if (!selectedModel) return

    setIsBenchmarking(true)
    setBenchmarkResults(null)

    try {
      // Note: This would require actual images for benchmarking
      // For now, we'll show a message
      setBenchmarkResults({
        message: 'Benchmarking requires test images. Use the Model Testing page to run benchmarks.',
        model: selectedModel
      })
    } catch (error: any) {
      console.error('Error benchmarking model:', error)
    } finally {
      setIsBenchmarking(false)
    }
  }

  if (modelsLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="xl" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Model Performance Dashboard</h1>
          <p className="text-gray-600 mt-2">Compare RE-ID model performance metrics</p>
        </div>
        <div className="flex gap-2">
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">Select model to benchmark</option>
            {modelNames.map((modelName) => (
              <option key={modelName} value={modelName}>
                {modelName}
              </option>
            ))}
          </select>
          <Button
            variant="primary"
            onClick={handleBenchmark}
            disabled={!selectedModel || isBenchmarking || benchmarkLoading}
          >
            {isBenchmarking || benchmarkLoading ? (
              <>
                <LoadingSpinner size="sm" className="mr-2" />
                Benchmarking...
              </>
            ) : (
              'Run Benchmark'
            )}
          </Button>
        </div>
      </div>

      {/* Model Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Accuracy Comparison */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <ChartBarIcon className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-semibold">Accuracy Comparison</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="model" />
              <YAxis domain={[0, 1]} />
              <Tooltip formatter={(value: number) => `${(value * 100).toFixed(1)}%`} />
              <Legend />
              <Bar dataKey="rank1_accuracy" fill="#3b82f6" name="Rank-1 Accuracy" />
              <Bar dataKey="map" fill="#10b981" name="mAP" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Performance Metrics */}
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <ClockIcon className="h-6 w-6 text-green-600" />
            <h2 className="text-xl font-semibold">Performance Metrics</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="model" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="latency_ms" stroke="#ef4444" name="Latency (ms)" />
              <Line type="monotone" dataKey="throughput" stroke="#8b5cf6" name="Throughput (img/s)" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Model Performance Table */}
      <Card>
        <div className="flex items-center gap-2 mb-4">
          <CpuChipIcon className="h-6 w-6 text-purple-600" />
          <h2 className="text-xl font-semibold">Model Performance Summary</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rank-1 Accuracy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  mAP
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Latency (ms)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Throughput (img/s)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {performanceData.map((model, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {model.model}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {(model.rank1_accuracy * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {(model.map * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {model.latency_ms.toFixed(0)}ms
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {model.throughput.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge variant="success">Available</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Benchmark Results */}
      {benchmarkResults && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Benchmark Results</h2>
          <Alert type="info">{benchmarkResults.message}</Alert>
        </Card>
      )}

      {/* Best Model Recommendation */}
      {performanceData.length > 0 && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">Best Model Recommendation</h2>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <span className="font-medium text-gray-900">Best Accuracy:</span>
              <span className="text-gray-700">
                {performanceData.reduce((best, current) =>
                  current.rank1_accuracy > best.rank1_accuracy ? current : best
                ).model}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <span className="font-medium text-gray-900">Fastest:</span>
              <span className="text-gray-700">
                {performanceData.reduce((fastest, current) =>
                  current.latency_ms < fastest.latency_ms ? current : fastest
                ).model}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
              <span className="font-medium text-gray-900">Best Throughput:</span>
              <span className="text-gray-700">
                {performanceData.reduce((best, current) =>
                  current.throughput > best.throughput ? current : best
                ).model}
              </span>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}

export default ModelDashboard

