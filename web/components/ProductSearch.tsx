'use client'

import { useState } from 'react'
import { Search, Loader2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useEAIChatAPI, type Product, type SearchParams } from '@/src/lib/api'
import { Badge } from '@/components/ui/badge'

export function ProductSearch() {
    const api = useEAIChatAPI()
    const [query, setQuery] = useState('')
    const [products, setProducts] = useState<Product[]>([])
    const [loading, setLoading] = useState(false)
    const [searchType, setSearchType] = useState<'semantic' | 'hybrid'>('semantic')

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!query.trim()) return

        setLoading(true)
        try {
            const params: SearchParams = {
                query,
                limit: 10,
            }

            if (searchType === 'hybrid') {
                params.hybrid = true
                params.alpha = 0.6
            }

            const results = await api.searchProducts(params)
            setProducts(results)
        } catch (error) {
            console.error('Search failed:', error)
            setProducts([])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Search className="w-5 h-5" />
                        Product Search
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSearch} className="space-y-4">
                        <div className="flex gap-2">
                            <Input
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Try: blue jacket, cotton shirt, electronics..."
                                className="flex-1"
                            />
                            <Button type="submit" disabled={loading || !query.trim()}>
                                {loading ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Search className="w-4 h-4" />
                                )}
                            </Button>
                        </div>

                        <div className="flex gap-2">
                            <Badge
                                variant={searchType === 'semantic' ? 'default' : 'outline'}
                                className="cursor-pointer"
                                onClick={() => setSearchType('semantic')}
                            >
                                <Sparkles className="w-3 h-3 mr-1" />
                                Semantic
                            </Badge>
                            <Badge
                                variant={searchType === 'hybrid' ? 'default' : 'outline'}
                                className="cursor-pointer"
                                onClick={() => setSearchType('hybrid')}
                            >
                                Hybrid
                            </Badge>
                        </div>
                    </form>
                </CardContent>
            </Card>

            {products.length > 0 && (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {products.map((product) => (
                        <Card key={product.id} className="hover:shadow-lg transition-shadow">
                            <CardContent className="p-4">
                                {product.image_url && (
                                    <img
                                        src={product.image_url}
                                        alt={product.title}
                                        className="w-full h-48 object-contain mb-3 rounded"
                                    />
                                )}
                                <h3 className="font-semibold text-sm mb-2 line-clamp-2">{product.title}</h3>
                                <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                                    {product.description}
                                </p>
                                <div className="flex justify-between items-center">
                                    <span className="text-lg font-bold text-primary">${product.price}</span>
                                    <Badge variant="outline">{product.category}</Badge>
                                </div>
                                <div className="mt-2 text-xs text-muted-foreground">
                                    Relevance: {(product.score * 100).toFixed(1)}%
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    )
}
