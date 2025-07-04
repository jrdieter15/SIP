/**
 * Call History Section Component
 * Displays call history with filtering and pagination
 */

export default {
    name: 'CallHistorySection',
    
    props: {
        callHistory: {
            type: Array,
            default: () => []
        },
        historyLoading: {
            type: Boolean,
            default: false
        },
        totalCount: {
            type: Number,
            default: 0
        },
        hasMore: {
            type: Boolean,
            default: false
        }
    },
    
    emits: [
        'refresh-history',
        'load-more',
        'filter-change',
        'call-details'
    ],
    
    data() {
        return {
            filterStatus: 'all',
            filterDateRange: 'week',
            showFilters: false
        };
    },
    
    computed: {
        filteredHistory() {
            let filtered = this.callHistory;
            
            if (this.filterStatus !== 'all') {
                filtered = filtered.filter(call => call.status === this.filterStatus);
            }
            
            return filtered;
        },
        
        statusOptions() {
            return [
                { value: 'all', label: 'All Calls' },
                { value: 'completed', label: 'Completed' },
                { value: 'failed', label: 'Failed' },
                { value: 'missed', label: 'Missed' }
            ];
        },
        
        dateRangeOptions() {
            return [
                { value: 'today', label: 'Today' },
                { value: 'week', label: 'This Week' },
                { value: 'month', label: 'This Month' },
                { value: 'all', label: 'All Time' }
            ];
        }
    },
    
    methods: {
        refreshHistory() {
            this.$emit('refresh-history');
        },
        
        loadMore() {
            this.$emit('load-more');
        },
        
        applyFilters() {
            this.$emit('filter-change', {
                status: this.filterStatus,
                dateRange: this.filterDateRange
            });
        },
        
        showCallDetails(call) {
            this.$emit('call-details', call);
        },
        
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
        
        formatDuration(seconds) {
            if (!seconds) return '0s';
            
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            
            if (minutes > 0) {
                return `${minutes}m ${remainingSeconds}s`;
            }
            
            return `${remainingSeconds}s`;
        },
        
        formatDateTime(dateString) {
            const date = new Date(dateString);
            return {
                date: date.toLocaleDateString(),
                time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
        },
        
        getStatusIcon(status) {
            const icons = {
                'completed': '✅',
                'failed': '❌',
                'missed': '📞',
                'initiated': '📤'
            };
            return icons[status] || '📞';
        },
        
        getCostDisplay(costCents) {
            if (!costCents) return 'Free';
            return `$${(costCents / 100).toFixed(2)}`;
        }
    },
    
    watch: {
        filterStatus() {
            this.applyFilters();
        },
        
        filterDateRange() {
            this.applyFilters();
        }
    },
    
    template: `
        <div class="call-history-section">
            <div class="history-header">
                <h3>Call History</h3>
                <div class="header-actions">
                    <button 
                        @click="showFilters = !showFilters" 
                        class="filter-btn"
                        :class="{ active: showFilters }">
                        🔍 Filters
                    </button>
                    <button 
                        @click="refreshHistory" 
                        class="refresh-btn" 
                        :disabled="historyLoading">
                        {{ historyLoading ? '⏳ Loading...' : '🔄 Refresh' }}
                    </button>
                </div>
            </div>

            <!-- Filters -->
            <div v-if="showFilters" class="filters-section">
                <div class="filter-group">
                    <label>Status:</label>
                    <select v-model="filterStatus" class="filter-select">
                        <option 
                            v-for="option in statusOptions" 
                            :key="option.value" 
                            :value="option.value">
                            {{ option.label }}
                        </option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label>Date Range:</label>
                    <select v-model="filterDateRange" class="filter-select">
                        <option 
                            v-for="option in dateRangeOptions" 
                            :key="option.value" 
                            :value="option.value">
                            {{ option.label }}
                        </option>
                    </select>
                </div>
            </div>

            <!-- History Table -->
            <div class="history-table">
                <div class="table-header">
                    <div class="col-status">Status</div>
                    <div class="col-number">Number</div>
                    <div class="col-datetime">Date & Time</div>
                    <div class="col-duration">Duration</div>
                    <div class="col-cost">Cost</div>
                    <div class="col-actions">Actions</div>
                </div>
                
                <div v-if="filteredHistory.length === 0 && !historyLoading" class="no-history">
                    <div class="empty-state">
                        <div class="empty-icon">📞</div>
                        <div class="empty-text">No call history available</div>
                        <div class="empty-subtext">Your calls will appear here once you make them</div>
                    </div>
                </div>
                
                <div v-if="historyLoading" class="loading-state">
                    <div class="loading-spinner"></div>
                    <div>Loading call history...</div>
                </div>
                
                <div 
                    v-for="call in filteredHistory" 
                    :key="call.call_id" 
                    class="history-row"
                    @click="showCallDetails(call)">
                    
                    <div class="col-status">
                        <span class="status-icon">{{ getStatusIcon(call.status) }}</span>
                        <span class="status-text">{{ call.status }}</span>
                    </div>
                    
                    <div class="col-number">
                        {{ formatPhoneNumber(call.destination_number) }}
                    </div>
                    
                    <div class="col-datetime">
                        <div class="datetime-display">
                            <div class="date">{{ formatDateTime(call.initiated_at).date }}</div>
                            <div class="time">{{ formatDateTime(call.initiated_at).time }}</div>
                        </div>
                    </div>
                    
                    <div class="col-duration">
                        {{ formatDuration(call.duration_seconds) }}
                    </div>
                    
                    <div class="col-cost">
                        {{ getCostDisplay(call.cost_cents) }}
                    </div>
                    
                    <div class="col-actions">
                        <button 
                            @click.stop="showCallDetails(call)"
                            class="action-btn details-btn">
                            📋 Details
                        </button>
                    </div>
                </div>
            </div>

            <!-- Load More -->
            <div v-if="hasMore" class="load-more-section">
                <button 
                    @click="loadMore" 
                    class="load-more-btn"
                    :disabled="historyLoading">
                    Load More Calls
                </button>
            </div>

            <!-- Summary -->
            <div v-if="totalCount > 0" class="history-summary">
                <div class="summary-item">
                    <span class="summary-label">Total Calls:</span>
                    <span class="summary-value">{{ totalCount }}</span>
                </div>
                <div class="summary-item">
                    <span class="summary-label">Showing:</span>
                    <span class="summary-value">{{ filteredHistory.length }}</span>
                </div>
            </div>
        </div>
    `
};