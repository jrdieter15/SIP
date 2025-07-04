/**
 * API Client for SIPCall Backend
 * Handles all HTTP requests to the FastAPI backend
 */

class SIPCallAPI {
    constructor() {
        this.baseURL = '/api/v1'; // Relative to current domain
        this.token = null;
        this.refreshToken = null;
        
        // Load tokens from localStorage if available
        this.loadTokens();
    }

    /**
     * Load tokens from localStorage
     */
    loadTokens() {
        try {
            this.token = localStorage.getItem('sipcall_access_token');
            this.refreshToken = localStorage.getItem('sipcall_refresh_token');
        } catch (error) {
            console.warn('Failed to load tokens from localStorage:', error);
        }
    }

    /**
     * Save tokens to localStorage
     */
    saveTokens(accessToken, refreshToken) {
        try {
            this.token = accessToken;
            this.refreshToken = refreshToken;
            localStorage.setItem('sipcall_access_token', accessToken);
            if (refreshToken) {
                localStorage.setItem('sipcall_refresh_token', refreshToken);
            }
        } catch (error) {
            console.warn('Failed to save tokens to localStorage:', error);
        }
    }

    /**
     * Clear tokens from memory and localStorage
     */
    clearTokens() {
        this.token = null;
        this.refreshToken = null;
        try {
            localStorage.removeItem('sipcall_access_token');
            localStorage.removeItem('sipcall_refresh_token');
        } catch (error) {
            console.warn('Failed to clear tokens from localStorage:', error);
        }
    }

    /**
     * Get authorization headers
     */
    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    /**
     * Make HTTP request with automatic token refresh
     */
    async request(method, endpoint, data = null, retryCount = 0) {
        const url = `${this.baseURL}${endpoint}`;
        const options = {
            method,
            headers: this.getAuthHeaders()
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            
            // Handle 401 Unauthorized - try to refresh token
            if (response.status === 401 && retryCount === 0 && this.refreshToken) {
                const refreshed = await this.refreshAccessToken();
                if (refreshed) {
                    // Retry the original request with new token
                    return this.request(method, endpoint, data, 1);
                } else {
                    // Refresh failed, clear tokens and throw error
                    this.clearTokens();
                    throw new Error('Authentication failed. Please log in again.');
                }
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API request failed: ${method} ${endpoint}`, error);
            throw error;
        }
    }

    /**
     * Authenticate with Nextcloud OAuth2 code
     */
    async authenticate(code, redirectUri) {
        try {
            const response = await this.request('POST', '/auth', {
                code,
                redirect_uri: redirectUri
            });

            this.saveTokens(response.access_token, response.refresh_token);
            return response;
        } catch (error) {
            console.error('Authentication failed:', error);
            throw error;
        }
    }

    /**
     * Refresh access token
     */
    async refreshAccessToken() {
        if (!this.refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${this.baseURL}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: this.refreshToken })
            });

            if (response.ok) {
                const data = await response.json();
                this.saveTokens(data.access_token, data.refresh_token);
                return true;
            } else {
                return false;
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    }

    /**
     * Initiate a new call
     */
    async initiateCall(destinationNumber, callerId = null, privacyMode = false) {
        return this.request('POST', '/call', {
            destination_number: destinationNumber,
            caller_id: callerId,
            privacy_mode: privacyMode
        });
    }

    /**
     * Get call status
     */
    async getCallStatus(callId) {
        return this.request('GET', `/call-status/${callId}`);
    }

    /**
     * Hangup call
     */
    async hangupCall(callId) {
        return this.request('POST', `/call/${callId}/hangup`);
    }

    /**
     * Hold/unhold call
     */
    async holdCall(callId, hold = true) {
        return this.request('POST', `/call/${callId}/hold`, { hold });
    }

    /**
     * Mute/unmute call
     */
    async muteCall(callId, muted = true) {
        return this.request('POST', `/call/${callId}/mute`, { muted });
    }

    /**
     * Get call history
     */
    async getCallHistory(limit = 50, offset = 0, fromDate = null, toDate = null) {
        const params = new URLSearchParams({
            limit: limit.toString(),
            offset: offset.toString()
        });

        if (fromDate) params.append('from_date', fromDate.toISOString());
        if (toDate) params.append('to_date', toDate.toISOString());

        return this.request('GET', `/call-history?${params}`);
    }

    /**
     * Get user profile
     */
    async getUserProfile() {
        return this.request('GET', '/user/profile');
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.token;
    }
}

// Export singleton instance
window.sipCallAPI = new SIPCallAPI();