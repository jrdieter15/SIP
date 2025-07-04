/**
 * SIPCall Vue.js Application - Modular Version
 * Main application component with modular architecture
 */

import DialpadSection from './components/DialpadSection.js';
import CallStatusSection from './components/CallStatusSection.js';
import CallHistorySection from './components/CallHistorySection.js';
import AdminDashboardSection from './components/AdminDashboardSection.js';

const SIPCallApp = {
    components: {
        DialpadSection,
        CallStatusSection,
        CallHistorySection,
        AdminDashboardSection
    },
    
    data() {
        return {
            // Authentication state
            isAuthenticated: false,
            user: null,
            
            // Call state
            currentCall: null,
            callStatus: 'idle',
            callDuration: 0,
            callTimer: null,
            
            // UI state
            destinationNumber: '',
            privacyMode: false,
            
            // Call history
            callHistory: [],
            historyLoading: false,
            totalCount: 0,
            hasMore: false,
            
            // Error handling
            error: null,
            loading: false,
            
            // Call controls
            isMuted: false,
            isOnHold: false,
            
            // Feature flags
            enterpriseFeaturesEnabled: false,
            availableFeatures: {
                core_features: [],
                enterprise_features: []
            }
        };
    },

    computed: {
        isCallActive() {
            return ['initiated', 'ringing', 'answered'].includes(this.callStatus);
        },
        
        isAdmin() {
            return this.user?.permissions?.is_admin || false;
        },
        
        showAdminDashboard() {
            return this.isAdmin && this.enterpriseFeaturesEnabled;
        }
    },

    async mounted() {
        await this.initializeApp();
    },

    beforeUnmount() {
        this.clearCallTimer();
        this.stopCallStatusPolling();
    },

    methods: {
        /**
         * Initialize the application
         */
        async initializeApp() {
            try {
                // Load available features
                await this.loadAvailableFeatures();
                
                // Check if user is authenticated
                if (window.sipCallAPI.isAuthenticated()) {
                    await this.loadUserProfile();
                    await this.loadCallHistory();
                } else {
                    // Handle OAuth2 callback if present
                    await this.handleOAuthCallback();
                }
            } catch (error) {
                console.error('App initialization failed:', error);
                this.showError('Failed to initialize application');
            }
        },
        
        /**
         * Load available features from backend
         */
        async loadAvailableFeatures() {
            try {
                const response = await fetch('/api/v1/features');
                if (response.ok) {
                    this.availableFeatures = await response.json();
                    this.enterpriseFeaturesEnabled = this.availableFeatures.enterprise_features.length > 0;
                }
            } catch (error) {
                console.error('Failed to load features:', error);
            }
        },

        /**
         * Handle OAuth2 callback from Nextcloud
         */
        async handleOAuthCallback() {
            const urlParams = new URLSearchParams(window.location.search);
            const code = urlParams.get('code');
            
            if (code) {
                try {
                    this.loading = true;
                    const redirectUri = window.location.origin + window.location.pathname;
                    
                    await window.sipCallAPI.authenticate(code, redirectUri);
                    await this.loadUserProfile();
                    await this.loadCallHistory();
                    
                    // Clean up URL
                    window.history.replaceState({}, document.title, window.location.pathname);
                } catch (error) {
                    this.showError('Authentication failed: ' + error.message);
                } finally {
                    this.loading = false;
                }
            }
        },

        /**
         * Load user profile
         */
        async loadUserProfile() {
            try {
                this.user = await window.sipCallAPI.getUserProfile();
                this.isAuthenticated = true;
            } catch (error) {
                console.error('Failed to load user profile:', error);
                this.isAuthenticated = false;
            }
        },

        /**
         * Load call history
         */
        async loadCallHistory() {
            try {
                this.historyLoading = true;
                const response = await window.sipCallAPI.getCallHistory(10);
                this.callHistory = response.calls;
                this.totalCount = response.total_count;
                this.hasMore = response.has_more;
            } catch (error) {
                console.error('Failed to load call history:', error);
                this.showError('Failed to load call history');
            } finally {
                this.historyLoading = false;
            }
        },

        // Dialpad Section Event Handlers
        handleStartCall() {
            this.startCall();
        },
        
        handleEndCall() {
            this.endCall();
        },
        
        handleAddDigit(digit) {
            this.destinationNumber += digit;
        },
        
        handleClearNumber() {
            this.destinationNumber = '';
        },
        
        handleDeleteDigit() {
            this.destinationNumber = this.destinationNumber.slice(0, -1);
        },

        // Call Status Section Event Handlers
        handleToggleMute() {
            this.toggleMute();
        },
        
        handleToggleHold() {
            this.toggleHold();
        },
        
        handleTransferCall() {
            // Implement call transfer functionality
            console.log('Transfer call requested');
        },

        // Call History Section Event Handlers
        handleRefreshHistory() {
            this.loadCallHistory();
        },
        
        handleLoadMore() {
            // Implement pagination
            console.log('Load more history requested');
        },
        
        handleFilterChange(filters) {
            // Implement filtering
            console.log('Filter change:', filters);
        },
        
        handleCallDetails(call) {
            // Show call details modal
            console.log('Show call details:', call);
        },

        /**
         * Initiate a new call
         */
        async startCall() {
            if (!this.destinationNumber.trim()) {
                this.showError('Please enter a phone number');
                return;
            }

            try {
                this.loading = true;
                this.clearError();
                
                const response = await window.sipCallAPI.initiateCall(
                    this.destinationNumber,
                    null, // caller_id
                    this.privacyMode
                );

                this.currentCall = response;
                this.callStatus = response.status;
                this.startCallStatusPolling();
                this.startCallTimer();

                console.log('Call initiated:', response);
            } catch (error) {
                console.error('Failed to start call:', error);
                this.showError('Failed to start call: ' + error.message);
                this.callStatus = 'failed';
            } finally {
                this.loading = false;
            }
        },

        /**
         * End the current call
         */
        async endCall() {
            if (!this.currentCall) return;

            try {
                this.loading = true;
                await window.sipCallAPI.hangupCall(this.currentCall.call_id);
                
                this.callStatus = 'completed';
                this.clearCallTimer();
                this.stopCallStatusPolling();
                
                // Reload call history
                await this.loadCallHistory();
                
                // Reset call state after a delay
                setTimeout(() => {
                    this.resetCallState();
                }, 2000);
            } catch (error) {
                console.error('Failed to end call:', error);
                this.showError('Failed to end call: ' + error.message);
            } finally {
                this.loading = false;
            }
        },

        /**
         * Toggle mute
         */
        async toggleMute() {
            if (!this.currentCall) return;

            try {
                const newMutedState = !this.isMuted;
                await window.sipCallAPI.muteCall(this.currentCall.call_id, newMutedState);
                this.isMuted = newMutedState;
            } catch (error) {
                console.error('Failed to toggle mute:', error);
                this.showError('Failed to toggle mute');
            }
        },

        /**
         * Toggle hold
         */
        async toggleHold() {
            if (!this.currentCall) return;

            try {
                const newHoldState = !this.isOnHold;
                await window.sipCallAPI.holdCall(this.currentCall.call_id, newHoldState);
                this.isOnHold = newHoldState;
                
                if (newHoldState) {
                    this.callStatus = 'on_hold';
                } else {
                    this.callStatus = 'answered';
                }
            } catch (error) {
                console.error('Failed to toggle hold:', error);
                this.showError('Failed to toggle hold');
            }
        },

        /**
         * Start polling for call status updates
         */
        startCallStatusPolling() {
            this.statusPollingInterval = setInterval(async () => {
                if (this.currentCall && this.isCallActive) {
                    try {
                        const status = await window.sipCallAPI.getCallStatus(this.currentCall.call_id);
                        this.callStatus = status.status;
                        
                        if (status.status === 'completed' || status.status === 'failed') {
                            this.stopCallStatusPolling();
                            this.clearCallTimer();
                            await this.loadCallHistory();
                            
                            setTimeout(() => {
                                this.resetCallState();
                            }, 2000);
                        }
                    } catch (error) {
                        console.error('Failed to get call status:', error);
                    }
                }
            }, 2000); // Poll every 2 seconds
        },

        /**
         * Stop call status polling
         */
        stopCallStatusPolling() {
            if (this.statusPollingInterval) {
                clearInterval(this.statusPollingInterval);
                this.statusPollingInterval = null;
            }
        },

        /**
         * Start call timer
         */
        startCallTimer() {
            this.callDuration = 0;
            this.callTimer = setInterval(() => {
                if (this.callStatus === 'answered') {
                    this.callDuration++;
                }
            }, 1000);
        },

        /**
         * Clear call timer
         */
        clearCallTimer() {
            if (this.callTimer) {
                clearInterval(this.callTimer);
                this.callTimer = null;
            }
        },

        /**
         * Reset call state
         */
        resetCallState() {
            this.currentCall = null;
            this.callStatus = 'idle';
            this.callDuration = 0;
            this.isMuted = false;
            this.isOnHold = false;
            this.destinationNumber = '';
        },

        /**
         * Show error message
         */
        showError(message) {
            this.error = message;
            setTimeout(() => {
                this.clearError();
            }, 5000);
        },

        /**
         * Clear error message
         */
        clearError() {
            this.error = null;
        }
    },

    template: `
        <div class="sipcall-app" :class="{ 'dark': document.documentElement.classList.contains('dark') }">
            <!-- Loading Overlay -->
            <div v-if="loading" class="loading-overlay">
                <div class="loading-spinner"></div>
                <p>Processing...</p>
            </div>

            <!-- Error Message -->
            <div v-if="error" class="error-message" @click="clearError">
                <span>{{ error }}</span>
                <button class="error-close">×</button>
            </div>

            <!-- Authentication Required -->
            <div v-if="!isAuthenticated" class="auth-required">
                <h3>Authentication Required</h3>
                <p>Please authenticate with Nextcloud to use SIP calling.</p>
            </div>

            <!-- Main App Content -->
            <div v-else class="app-content">
                <!-- Header -->
                <div class="app-header">
                    <h2>SIP Integration</h2>
                    <div class="user-info" v-if="user">
                        Welcome, {{ user.display_name || user.email }}
                        <span v-if="isAdmin" class="admin-badge">Admin</span>
                    </div>
                </div>

                <!-- Feature Availability Notice -->
                <div v-if="enterpriseFeaturesEnabled" class="feature-notice enterprise">
                    🚀 Enterprise features are available
                </div>
                <div v-else class="feature-notice core">
                    📞 Core calling features are available
                </div>

                <!-- Admin Dashboard (Enterprise Feature) -->
                <AdminDashboardSection 
                    v-if="showAdminDashboard"
                    :user="user"
                />

                <!-- Call Interface -->
                <div class="call-interface">
                    <!-- Dialpad Section -->
                    <DialpadSection
                        v-model:destination-number="destinationNumber"
                        v-model:privacy-mode="privacyMode"
                        :is-call-active="isCallActive"
                        :loading="loading"
                        @start-call="handleStartCall"
                        @end-call="handleEndCall"
                        @add-digit="handleAddDigit"
                        @clear-number="handleClearNumber"
                        @delete-digit="handleDeleteDigit"
                    />

                    <!-- Call Status Section -->
                    <CallStatusSection
                        :call-status="callStatus"
                        :call-duration="callDuration"
                        :is-call-active="isCallActive"
                        :is-muted="isMuted"
                        :is-on-hold="isOnHold"
                        :current-call="currentCall"
                        @toggle-mute="handleToggleMute"
                        @toggle-hold="handleToggleHold"
                        @transfer-call="handleTransferCall"
                    />
                </div>

                <!-- Call History -->
                <CallHistorySection
                    :call-history="callHistory"
                    :history-loading="historyLoading"
                    :total-count="totalCount"
                    :has-more="hasMore"
                    @refresh-history="handleRefreshHistory"
                    @load-more="handleLoadMore"
                    @filter-change="handleFilterChange"
                    @call-details="handleCallDetails"
                />
            </div>
        </div>
    `
};

// Initialize the Vue app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const { createApp } = Vue;
    createApp(SIPCallApp).mount('#sipcall-app');
});