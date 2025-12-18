'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { MessageSquare, Database, Zap, Search, ArrowRight, CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

interface ServiceStatus {
    name: string
    status: 'healthy' | 'unhealthy' | 'loading'
    url: string
}

export default function HomePage() {
    const [services, setServices] = useState<ServiceStatus[]>([
        { name: 'API', status: 'loading', url: 'http://localhost:8000' },
        { name: 'Qdrant', status: 'loading', url: 'http://localhost:6333' },
        { name: 'phpMyAdmin', status: 'loading', url: 'http://localhost:8080' },
        { name: 'Temporal UI', status: 'loading', url: 'http://localhost:8088' },
        { name: 'Langfuse', status: 'loading', url: 'http://localhost:8081' },
    ])
    const [chatInput, setChatInput] = useState('')

    useEffect(() => {
        const checkService = async (name: string, url: string): Promise<ServiceStatus> => {
            try {
                const controller = new AbortController()
                const timeout = setTimeout(() => controller.abort(), 3000)

                const healthUrl = name === 'API' ? `${url}/health` : url
                await fetch(healthUrl, {
                    mode: 'no-cors',
                    signal: controller.signal
                })
                clearTimeout(timeout)
                return { name, status: 'healthy', url }
            } catch {
                return { name, status: 'unhealthy', url }
            }
        }

        const checkAllServices = async () => {
            const results = await Promise.all(
                services.map(s => checkService(s.name, s.url))
            )
            setServices(results)
        }

        checkAllServices()
        const interval = setInterval(checkAllServices, 30000)
        return () => clearInterval(interval)
    }, [])

    const features = [
        {
            icon: MessageSquare,
            title: 'AI-Powered Chat',
            description: 'Multi-LLM support with OpenAI, Anthropic, and Gemini. Intelligent product recommendations.',
        },
        {
            icon: Database,
            title: 'Vector Search',
            description: 'Qdrant-powered semantic search with real-time product indexing and RAG retrieval.',
        },
        {
            icon: Zap,
            title: 'Workflow Automation',
            description: 'Temporal-based orchestration for background tasks, reindexing, and data sync.',
        },
        {
            icon: Search,
            title: 'Smart Discovery',
            description: 'Natural language queries with filtering, intent detection, and personalized results.',
        },
    ]

    return (
        <main className="container mx-auto px-4 py-8">
            {/* Hero Section */}
            <div className="text-center mb-12">
                <div className="inline-flex items-center px-3 py-1 rounded-full bg-primary/10 text-primary text-sm mb-4">
                    <Zap className="w-4 h-4 mr-2" />
                    Production-Grade AI Platform
                </div>
                <h1 className="text-5xl font-bold tracking-tight mb-4 bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
                    eaichat
                </h1>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
                    AI-powered e-commerce platform with vector search, multi-LLM orchestration,
                    and real-time recommendations.
                </p>

                {/* Quick Chat Input */}
                <div className="flex max-w-md mx-auto gap-2">
                    <Input
                        placeholder="Try: Find me a blue jacket under $50..."
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        className="flex-1"
                    />
                    <Button>
                        <ArrowRight className="w-4 h-4" />
                    </Button>
                </div>
            </div>

            {/* Features Grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                {features.map((feature, index) => (
                    <Card key={index} className="hover:border-primary/50 transition-colors">
                        <CardHeader>
                            <feature.icon className="w-10 h-10 text-primary mb-2" />
                            <CardTitle className="text-lg">{feature.title}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <CardDescription>{feature.description}</CardDescription>
                        </CardContent>
                    </Card>
                ))}
            </div>

            {/* Service Status */}
            <Card className="mb-12">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Database className="w-5 h-5" />
                        Service Status
                    </CardTitle>
                    <CardDescription>Real-time health monitoring of all backend services</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        {services.map((service, index) => (
                            <a
                                key={index}
                                href={service.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 p-3 rounded-lg border hover:border-primary/50 transition-colors"
                            >
                                {service.status === 'loading' ? (
                                    <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                                ) : service.status === 'healthy' ? (
                                    <CheckCircle className="w-4 h-4 text-green-500" />
                                ) : (
                                    <AlertCircle className="w-4 h-4 text-red-500" />
                                )}
                                <span className="text-sm font-medium">{service.name}</span>
                            </a>
                        ))}
                    </div>
                </CardContent>
            </Card>

            {/* Quick Links */}
            <div className="grid md:grid-cols-3 gap-6">
                <Card>
                    <CardHeader>
                        <CardTitle>API Documentation</CardTitle>
                        <CardDescription>Explore the FastAPI auto-generated docs</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button variant="outline" asChild className="w-full">
                            <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
                                View OpenAPI Docs
                            </a>
                        </Button>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Vector Database</CardTitle>
                        <CardDescription>Manage Qdrant collections and vectors</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button variant="outline" asChild className="w-full">
                            <a href="http://localhost:6333/dashboard" target="_blank" rel="noopener noreferrer">
                                Qdrant Dashboard
                            </a>
                        </Button>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Workflow Monitor</CardTitle>
                        <CardDescription>View Temporal workflows and activities</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Button variant="outline" asChild className="w-full">
                            <a href="http://localhost:8088" target="_blank" rel="noopener noreferrer">
                                Temporal UI
                            </a>
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </main>
    )
}
