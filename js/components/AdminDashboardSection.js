/**
 * Admin Dashboard Section Component
 * Enterprise feature for system administration
 */

export default {
    name: 'AdminDashboardSection',
    
    props: {
        user: {
            type: Object,
            required: true
        }
    },
    
    data() {
        return {
            systemMetrics: null,
            users: [],
            systemConfig: null,
            analytics: null,
            loading: false,
            error: null,
            activeTab: 'overview'
        };
    },
    
    computed: {
        isAdmin() {
            return this.user?.permissions?.is_admin || false;
        },
        
        tabs() {
            return [
                { id: 'overview', label: 'Overview', icon: '📊' },
                { id: 'users', label: 'Users', icon: '👥' },
                { id: 'analytics', label: 'Analytics', icon: '📈' },
                { id: 'config', label: 'Configuration', icon: '⚙️' }
            ];
        }
    },
    
    async mounted() {
        if (this.isAdmin) {
            await this.loadDashboardData();
        }
    },
    
    methods: {
        async loadDashboardData() {
            this.loading = true;
            this.error = null;
            
            try {
                await Promise.all([
                    this.loadSystemMetrics(),
                    this.loadUsers(),
                    this.loadSystemConfig(),
                    this.loadAnalytics()
                ]);
            } catch (error) {
                this.error = 'Failed to load dashboard data: ' + error.message;
            } finally {
                this.loading = false;
            }
        },
        
        async loadSystemMetrics() {
            try {
                const response = await fetch('/api/v1/admin/metrics', {
                    headers: {
                        'Authorization': `Bearer ${window.sipCallAPI.token}`
                    }
                });
                
                if (response.ok) {
                    this.systemMetrics = await response.json();
                }
            } catch (error) {
                console.error('Failed to load system metrics:', error);
            }
        },
        
        async loadUsers() {
            try {
                const response = await fetch('/api/v1/admin/users', {
                    headers: {
                        'Authorization': `Bearer ${window.sipCallAPI.token}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    this.users = data.users;
                }
            } catch (error) {
                console.error('Failed to load users:', error);
            }
        },
        
        async loadSystemConfig() {
            try {
                const response = await fetch('/api/v1/admin/system-config', {
                    headers: {
                        'Authorization': `Bearer ${window.sipCallAPI.token}`
                    }
                });
                
                if (response.ok) {
                    this.systemConfig = await response.json();
                }
            } catch (error) {
                console.error('Failed to load system config:', error);
            }
        },
        
        async loadAnalytics() {
            try {
                const response = await fetch('/api/v1/analytics/calls', {
                    headers: {
                        'Authorization': `Bearer ${window.sipCallAPI.token}`
                    }
                });
                
                if (response.ok) {
                    this.analytics = await response.json();
                }
            } catch (error) {
                console.error('Failed to load analytics:', error);
            }
        },
        
        setActiveTab(tabId) {
            this.activeTab = tabId;
        },
        
        formatCurrency(cents) {
            return `$${(cents / 100).toFixed(2)}`;
        },
        
        getStatusColor(status) {
            const colors = {
                'healthy': 'green',
                'connected': 'green',
                'warning': 'orange',
                'error': 'red'
            };
            return colors[status] || 'gray';
        }
    },
    
    template: `
        <div v-if="isAdmin" class="admin-dashboard-section">
            <div class="dashboard-header">
                <h3>🛠️ Admin Dashboard</h3>
                <button @click="loadDashboardData" class="refresh-btn" :disabled="loading">
                    {{ loading ? '⏳ Loading...' : '🔄 Refresh' }}
                </button>
            </div>

            <!-- Error Display -->
            <div v-if="error" class="error-message">
                {{ error }}
            </div>

            <!-- Tab Navigation -->
            <div class="tab-navigation">
                <button 
                    v-for="tab in tabs" 
                    :key="tab.id"
                    @click="setActiveTab(tab.id)"
                    class="tab-btn"
                    :class="{ active: activeTab === tab.id }">
                    {{ tab.icon }} {{ tab.label }}
                </button>
            </div>

            <!-- Overview Tab -->
            <div v-if="activeTab === 'overview'" class="tab-content">
                <div v-if="systemMetrics" class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-icon">📞</div>
                        <div class="metric-value">{{ systemMetrics.active_calls }}</div>
                        <div class="metric-label">Active Calls</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-icon">👥</div>
                        <div class="metric-value">{{ systemMetrics.total_users }}</div>
                        <div class="metric-label">Total Users</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-icon">💚</div>
                        <div class="metric-value" :style="{ color: getStatusColor(systemMetrics.system_health) }">
                            {{ systemMetrics.system_health }}
                        </div>
                        <div class="metric-label">System Health</div>
                    </div>
                    
                    <div class="metric-card">
                        <div class="metric-icon">🗄️</div>
                        <div class="metric-value" :style="{ color: getStatusColor(systemMetrics.database_status) }">
                            {{ systemMetrics.database_status }}
                        </div>
                        <div class="metric-label">Database</div>
                    </div>
                </div>

                <!-- System Status -->
                <div v-if="systemConfig" class="system-status">
                    <h4>System Status</h4>
                    <div class="status-grid">
                        <div class="status-item">
                            <span class="status-label">SIP Provider:</span>
                            <span class="status-value">{{ systemConfig.sip_provider.name }}</span>
                            <span class="status-indicator" :style="{ color: getStatusColor(systemConfig.sip_provider.status) }">
                                ● {{ systemConfig.sip_provider.status }}
                            </span>
                        </div>
                        
                        <div class="status-item">
                            <span class="status-label">Account Balance:</span>
                            <span class="status-value">{{ formatCurrency(systemConfig.sip_provider.balance_cents) }}</span>
                        </div>
                        
                        <div class="status-item">
                            <span class="status-label">Encryption:</span>
                            <span class="status-value">{{ systemConfig.security.encryption_enabled ? 'Enabled' : 'Disabled' }}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Users Tab -->
            <div v-if="activeTab === 'users'" class="tab-content">
                <div class="users-section">
                    <h4>User Management</h4>
                    <div class="users-table">
                        <div class="table-header">
                            <div>Username</div>
                            <div>Email</div>
                            <div>Total Calls</div>
                            <div>Last Call</div>
                            <div>Status</div>
                        </div>
                        
                        <div v-for="user in users" :key="user.user_id" class="user-row">
                            <div>{{ user.username }}</div>
                            <div>{{ user.email }}</div>
                            <div>{{ user.total_calls }}</div>
                            <div>{{ user.last_call ? new Date(user.last_call).toLocaleDateString() : 'Never' }}</div>
                            <div>
                                <span class="status-badge" :class="{ active: user.is_active }">
                                    {{ user.is_active ? 'Active' : 'Inactive' }}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Analytics Tab -->
            <div v-if="activeTab === 'analytics'" class="tab-content">
                <div v-if="analytics" class="analytics-section">
                    <h4>Call Analytics</h4>
                    <div class="analytics-grid">
                        <div class="analytics-card">
                            <h5>Call Statistics</h5>
                            <div class="stat-item">
                                <span>Total Calls:</span>
                                <span>{{ analytics.total_calls }}</span>
                            </div>
                            <div class="stat-item">
                                <span>Successful:</span>
                                <span>{{ analytics.successful_calls }}</span>
                            </div>
                            <div class="stat-item">
                                <span>Failed:</span>
                                <span>{{ analytics.failed_calls }}</span>
                            </div>
                            <div class="stat-item">
                                <span>Success Rate:</span>
                                <span>{{ Math.round((analytics.successful_calls / analytics.total_calls) * 100) }}%</span>
                            </div>
                        </div>
                        
                        <div class="analytics-card">
                            <h5>Performance</h5>
                            <div class="stat-item">
                                <span>Avg Duration:</span>
                                <span>{{ Math.round(analytics.average_duration) }}s</span>
                            </div>
                            <div class="stat-item">
                                <span>Total Cost:</span>
                                <span>{{ formatCurrency(analytics.total_cost * 100) }}</span>
                            </div>
                            <div class="stat-item">
                                <span>Peak Hours:</span>
                                <span>{{ analytics.peak_hours.join(', ') }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Configuration Tab -->
            <div v-if="activeTab === 'config'" class="tab-content">
                <div v-if="systemConfig" class="config-section">
                    <h4>System Configuration</h4>
                    <div class="config-grid">
                        <div class="config-group">
                            <h5>Rate Limits</h5>
                            <div class="config-item">
                                <label>Calls per minute:</label>
                                <span>{{ systemConfig.rate_limits.calls_per_minute }}</span>
                            </div>
                            <div class="config-item">
                                <label>Calls per day:</label>
                                <span>{{ systemConfig.rate_limits.calls_per_day }}</span>
                            </div>
                        </div>
                        
                        <div class="config-group">
                            <h5>Security Settings</h5>
                            <div class="config-item">
                                <label>Encryption:</label>
                                <span>{{ systemConfig.security.encryption_enabled ? 'Enabled' : 'Disabled' }}</span>
                            </div>
                            <div class="config-item">
                                <label>Audit Logging:</label>
                                <span>{{ systemConfig.security.audit_logging ? 'Enabled' : 'Disabled' }}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `
};