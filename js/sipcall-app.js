/**
 * SIPCall Vue.js Application
 * Main application component with call functionality
 */

import { createApp } from 'vue';

const SIPCallApp = {
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
            isDialpadVisible: true,
            
            // Call history
            callHistory: [],
            historyLoading: false,
            
            // Error handling
            error: null,
            loading: false,
            
            // Call controls
            isMuted: false,
            isOnHold: false
        };
    },

    computed: {
        /**
         * Format call duration for display
         */
        formattedDuration() {
            const minutes = Math.floor(this.callDuration / 60);
            const seconds = this.callDuration % 60;
            return `${minutes}:${seconds.toString().padStart(2, '0')}`;
        },

        /**
         * Check if call is active
         */
        isCallActive() {
            return ['initiated', 'ringing', 'answered'].includes(this.callStatus);
        },

        /**
         * Get call status display text
         */
        callStatusText() {
            const statusMap = {
                'idle': 'Idle',
                'initiated': 'Connecting...',
                'ringing': 'Ringing...',
                'answered': 'In Progress',
                'completed': 'Call Ended',
                'failed': 'Call Failed',
                'on_hold': 'On Hold'
            };
            return statusMap[this.callStatus] || this.callStatus;
        }
    },

    async mounted() {
        await this.initializeApp();
    },

    beforeUnmount() {
        this.clearCallTimer();
    },

    methods: {
        /**
         * Initialize the application
         */
        async initializeApp() {
            try {
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
            } catch (error) {
                console.error('Failed to load call history:', error);
                this.showError('Failed to load call history');
            } finally {
                this.historyLoading = false;
            }
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
         * Add digit to destination number
         */
        addDigit(digit) {
            this.destinationNumber += digit;
        },

        /**
         * Clear destination number
         */
        clearNumber() {
            this.destinationNumber = '';
        },

        /**
         * Delete last digit
         */
        deleteDigit() {
            this.destinationNumber = this.destinationNumber.slice(0, -1);
        },

        /**
         * Format phone number for display
         */
        formatPhoneNumber(number) {
            if (!number) return '';
            
            // Simple formatting - can be enhanced
            if (number.startsWith('+')) {
                return number;
            }
            
            // Add formatting based on length
            if (number.length === 10) {
                return `(${number.slice(0, 3)}) ${number.slice(3, 6)}-${number.slice(6)}`;
            }
            
            return number;
        },

        /**
         * Format call duration
         */
        formatDuration(seconds) {
            if (!seconds) return '0s';
            
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            
            if (minutes > 0) {
                return `${minutes}m ${remainingSeconds}s`;
            }
            
            return `${remainingSeconds}s`;
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
        },

        /**
         * Toggle privacy mode
         */
        togglePrivacyMode() {
            this.privacyMode = !this.privacyMode;
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
                    </div>
                </div>

                <!-- Call Interface -->
                <div class="call-interface">
                    <!-- Dialpad Section -->
                    <div class="dialpad-section">
                        <div class="number-input">
                            <input 
                                v-model="destinationNumber" 
                                type="tel" 
                                placeholder="Enter phone number"
                                class="phone-input"
                                :disabled="isCallActive"
                                @keyup.enter="startCall"
                            />
                        </div>

                        <!-- Dialpad Grid -->
                        <div class="dialpad-grid" v-if="isDialpadVisible">
                            <button v-for="digit in ['1','2','3','4','5','6','7','8','9','*','0','#']" 
                                    :key="digit"
                                    @click="addDigit(digit)"
                                    class="dialpad-button"
                                    :disabled="isCallActive">
                                {{ digit }}
                            </button>
                        </div>

                        <!-- Call Actions -->
                        <div class="call-actions">
                            <button v-if="!isCallActive" 
                                    @click="startCall" 
                                    class="start-call-btn"
                                    :disabled="!destinationNumber.trim() || loading">
                                Start Call
                            </button>
                            
                            <button v-if="isCallActive" 
                                    @click="endCall" 
                                    class="end-call-btn"
                                    :disabled="loading">
                                End Call
                            </button>
                        </div>
                    </div>

                    <!-- Call Status Section -->
                    <div class="call-status-section">
                        <div class="status-header">
                            <h3>Call Status</h3>
                        </div>
                        
                        <div class="status-display">
                            <div class="status-text">{{ callStatusText }}</div>
                            <div v-if="callStatus === 'answered'" class="call-duration">
                                {{ formattedDuration }}
                            </div>
                        </div>

                        <!-- Call Controls -->
                        <div v-if="isCallActive" class="call-controls">
                            <button @click="toggleMute" 
                                    class="control-btn"
                                    :class="{ active: isMuted }">
                                {{ isMuted ? 'Unmute' : 'Mute' }}
                            </button>
                            
                            <button @click="toggleHold" 
                                    class="control-btn"
                                    :class="{ active: isOnHold }">
                                {{ isOnHold ? 'Resume' : 'Hold' }}
                            </button>
                        </div>

                        <!-- Privacy Mode -->
                        <div class="privacy-section">
                            <h4>Privacy Mode</h4>
                            <div class="privacy-toggle">
                                <label class="toggle-label">
                                    <input type="checkbox" 
                                           v-model="privacyMode"
                                           :disabled="isCallActive">
                                    <span class="toggle-slider"></span>
                                    Ephemeral Session
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Call History -->
                <div class="call-history-section">
                    <div class="history-header">
                        <h3>Call History</h3>
                        <button @click="loadCallHistory" class="refresh-btn" :disabled="historyLoading">
                            {{ historyLoading ? 'Loading...' : 'Refresh' }}
                        </button>
                    </div>

                    <div class="history-table">
                        <div class="table-header">
                            <div class="col-time">Time</div>
                            <div class="col-duration">Duration</div>
                            <div class="col-destination">Destination</div>
                        </div>
                        
                        <div v-if="callHistory.length === 0" class="no-history">
                            No call history available
                        </div>
                        
                        <div v-for="call in callHistory" 
                             :key="call.call_id" 
                             class="history-row">
                            <div class="col-time">
                                {{ new Date(call.initiated_at).toLocaleTimeString() }}
                            </div>
                            <div class="col-duration">
                                {{ formatDuration(call.duration_seconds) }}
                            </div>
                            <div class="col-destination">
                                {{ formatPhoneNumber(call.destination_number) }}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};

// Initialize the Vue app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    createApp(SIPCallApp).mount('#sipcall-app');
});