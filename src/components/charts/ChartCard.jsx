import { Card, ErrorState } from '../ui/Card'
import { ChartSkeleton } from '../ui/Skeleton'

/**
 * Card that shows a skeleton while loading, an error with retry on failure,
 * and the chart once data has arrived.
 */
export default function ChartCard({ title, query, skeleton = <ChartSkeleton />, height = 'h-64', className = '', children }) {
  const { data, loading, error, reload } = query
  return (
    <Card title={title} className={className} bodyClassName={`relative p-4 ${height}`}>
      {loading ? skeleton : error ? <ErrorState error={error} onRetry={reload} /> : data && children(data)}
    </Card>
  )
}
