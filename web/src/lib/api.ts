/**
 * eaichat API Client
 * ====================
 * 
 * Client library for interacting with the eaichat backend API.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Product {
    id: string;
    score: number;
    title: string;
    description: string;
    price: number;
    category: string;
    image_url?: string;
    platform: string;
    rating?: number;
    in_stock?: boolean;
}

export interface SearchParams {
    query: string;
    limit?: number;
    category?: string;
    min_price?: number;
    max_price?: number;
    platform?: string;
    hybrid?: boolean;
    alpha?: number;
}

export interface SyncParams {
    platform: string;
    batch_size?: number;
}

export interface SyncResponse {
    status: string;
    message: string;
    job_id: string;
}

export interface CollectionStats {
    status: string;
    collection?: string;
    points_count?: number;
    error?: string;
}

export interface HealthResponse {
    status: string;
    version?: string;
    services?: Record<string, string>;
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
}

export interface ChatRequest {
    message: string;
    use_rag?: boolean;
    provider?: 'openai' | 'anthropic' | 'gemini';
}

export interface ChatResponse {
    message: string;
    products?: Product[];
    provider?: string;
    tokens_used?: number;
}

/**
 * eaichat API Client
 */
export class EAIChatAPI {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    /**
     * Health check
     */
    async health(): Promise<HealthResponse> {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.json();
    }

    /**
     * Create collection
     */
    async createCollection(recreate: boolean = false): Promise<any> {
        const response = await fetch(`${this.baseUrl}/api/index/create-collection`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ recreate }),
        });
        return response.json();
    }

    /**
     * Trigger product sync via Temporal workflow
     */
    async syncProducts(params: SyncParams): Promise<SyncResponse> {
        const response = await fetch(`${this.baseUrl}/api/index/sync`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        return response.json();
    }

    /**
     * Get collection statistics
     */
    async getStats(): Promise<CollectionStats> {
        const response = await fetch(`${this.baseUrl}/api/index/stats`);
        return response.json();
    }

    /**
     * Search products
     */
    async searchProducts(params: SearchParams): Promise<Product[]> {
        const response = await fetch(`${this.baseUrl}/api/index/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        return response.json();
    }

    /**
     * Send chat message
     */
    async sendChatMessage(params: ChatRequest): Promise<ChatResponse> {
        const response = await fetch(`${this.baseUrl}/api/chat/send`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params),
        });
        return response.json();
    }

    /**
     * Stream chat response (SSE)
     */
    streamChat(params: ChatRequest, onToken: (token: string) => void, onDone: () => void): void {
        const eventSource = new EventSource(
            `${this.baseUrl}/api/chat/stream?` + new URLSearchParams({
                message: params.message,
                use_rag: String(params.use_rag ?? true),
                provider: params.provider ?? 'openai',
            })
        );

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'token') {
                onToken(data.content);
            } else if (data.type === 'done') {
                eventSource.close();
                onDone();
            }
        };

        eventSource.onerror = () => {
            eventSource.close();
            onDone();
        };
    }

    /**
     * Get available LLM providers
     */
    async getProviders(): Promise<any> {
        const response = await fetch(`${this.baseUrl}/api/chat/providers`);
        return response.json();
    }
}

/**
 * Default API client instance
 */
export const apiClient = new EAIChatAPI();

/**
 * React hooks for API calls
 */
export function useEAIChatAPI() {
    return {
        health: () => apiClient.health(),
        createCollection: (recreate?: boolean) => apiClient.createCollection(recreate),
        syncProducts: (params: SyncParams) => apiClient.syncProducts(params),
        getStats: () => apiClient.getStats(),
        searchProducts: (params: SearchParams) => apiClient.searchProducts(params),
        sendChatMessage: (params: ChatRequest) => apiClient.sendChatMessage(params),
        streamChat: (params: ChatRequest, onToken: (token: string) => void, onDone: () => void) =>
            apiClient.streamChat(params, onToken, onDone),
        getProviders: () => apiClient.getProviders(),
    };
}
