'use client'

import { useState, useEffect } from 'react'
import { Database, Loader2, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useEAIChatAPI } from '@/src/lib/api'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'

export function SyncManager() {
    const api = useEAIChatAPI()
    const [syncing, setSyncing] = useState(false)
    const [lastJobId, setLastJobId] = useState<string>('')
    const [stats, setStats] = useState<{ points_count?: number; status: string }>({ status: 'loading' })
    const [batchSize, setBatchSize] = useState('10')

    const loadStats = async () => {
        try {
            const data = await api.getStats()
            setStats(data)
        } catch (error) {
            console.error('Failed to load stats:', error)
            setStats({ status: 'error' })
        }
    }

    useEffect(() => {
        loadStats()
        const interval = setInterval(loadStats, 10000) // Refresh every 10s
        return () => clearInterval(interval)
    }, [])

    const handleSync = async () => {
        setSyncing(true)
        try {
            const result = await api.syncProducts({
                platform: 'fakestore',
                batch_size: parseInt(batchSize) || 10,
            })
            setLastJobId(result.job_id)

            // Reload stats after a delay
            setTimeout(loadStats, 5000)
        } catch (error) {
            console.error('Sync failed:', error)
        } finally {
            setSyncing(false)
        }
    }

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Database className="w-5 h-5" />
                        Collection Stats
                    </CardTitle>
                    <CardDescription>Real-time product indexing status</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center gap-4">
                        {stats.status === 'ok' ? (
                            <>
                                <CheckCircle className="w-8 h-8 text-green-500" />
                                <div>
                                    <div className="text-3xl font-bold">{stats.points_count || 0}</div>
                                    <div className="text-sm text-muted-foreground">Products Indexed</div>
                                </div>
                            </>
                        ) : (
                            <>
                                <AlertCircle className="w-8 h-8 text-yellow-500" />
                                <div className="text-sm text-muted-foreground">Loading...</div>
                            </>
                        )}
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>Sync Products</CardTitle>
                    <CardDescription>Trigger Temporal workflow to index products from platform</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex gap-2 items-end">
                        <div className="flex-1">
                            <label className="text-sm font-medium mb-1 block">Batch Size</label>
                            <Input
                                type="number"
                                value={batchSize}
                                onChange={(e) => setBatchSize(e.target.value)}
                                min="1"
                                max="100"
                                placeholder="10"
                            />
                        </div>
                        <Button onClick={handleSync} disabled={syncing} className="px-8">
                            {syncing ? (
                                <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Syncing...
                                </>
                            ) : (
                                'Start Sync'
                            )}
                        </Button>
                    </div>

                    {lastJobId && (
                        <div className="pt-4 border-t">
                            <div className="text-sm font-medium mb-1">Last Workflow</div>
                            <div className="flex items-center gap-2">
                                <Badge variant="outline" className="font-mono text-xs">
                                    {lastJobId}
                                </Badge>
                                <a
                                    href={`http://localhost:8088/namespaces/default/workflows/${lastJobId}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-xs text-primary hover:underline"
                                >
                                    View in Temporal UI →
                                </a>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
