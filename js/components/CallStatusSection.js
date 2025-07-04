/**
 * Call Status Section Component
 * Displays call status, duration, and controls
 */

export default {
    name: 'CallStatusSection',
    
    props: {
        callStatus: {
            type: String,
            default: 'idle'
        },
        callDuration: {
            type: Number,
            default: 0
        },
        isCallActive: {
            type: Boolean,
            default: false
        },
        isMuted: {
            type: Boolean,
            default: false
        },
        isOnHold: {
            type: Boolean,
            default: false
        },
        currentCall: {
            type: Object,
            default: null
        }
    },
    
    emits: [
        'toggle-mute',
        'toggle-hold',
        'transfer-call'
    ],
    
    computed: {
        formattedDuration() {
            const minutes = Math.floor(this.callDuration / 60);
            const seconds = this.callDuration % 60;
            return `${minutes}:${seconds.toString().padStart(2, '0')}`;
        },
        
        callStatusText() {
            const statusMap = {
                'idle': 'Ready to call',
                'initiated': 'Connecting...',
                'ringing': 'Ringing...',
                'answered': 'In Progress',
                'completed': 'Call Ended',
                'failed': 'Call Failed',
                'on_hold': 'On Hold'
            };
            return statusMap[this.callStatus] || this.callStatus;
        },
        
        statusClass() {
            return {
                'status-idle': this.callStatus === 'idle',
                'status-active': ['initiated', 'ringing', 'answered'].includes(this.callStatus),
                'status-hold': this.callStatus === 'on_hold',
                'status-ended': ['completed', 'failed'].includes(this.callStatus)
            };
        }
    },
    
    methods: {
        toggleMute() {
            this.$emit('toggle-mute');
        },
        
        toggleHold() {
            this.$emit('toggle-hold');
        },
        
        transferCall() {
            this.$emit('transfer-call');
        }
    },
    
    template: `
        <div class="call-status-section">
            <div class="status-header">
                <h3>Call Status</h3>
            </div>
            
            <div class="status-display" :class="statusClass">
                <div class="status-text">{{ callStatusText }}</div>
                
                <div v-if="currentCall" class="call-info">
                    <div class="call-id">Call ID: {{ currentCall.call_id }}</div>
                    <div class="destination">To: {{ currentCall.destination_number }}</div>
                </div>
                
                <div v-if="callStatus === 'answered'" class="call-duration">
                    {{ formattedDuration }}
                </div>
                
                <div v-if="isCallActive" class="call-indicators">
                    <span v-if="isMuted" class="indicator muted">🔇 Muted</span>
                    <span v-if="isOnHold" class="indicator hold">⏸️ On Hold</span>
                </div>
            </div>

            <!-- Call Controls -->
            <div v-if="isCallActive" class="call-controls">
                <button 
                    @click="toggleMute" 
                    class="control-btn"
                    :class="{ active: isMuted }">
                    {{ isMuted ? '🔊 Unmute' : '🔇 Mute' }}
                </button>
                
                <button 
                    @click="toggleHold" 
                    class="control-btn"
                    :class="{ active: isOnHold }">
                    {{ isOnHold ? '▶️ Resume' : '⏸️ Hold' }}
                </button>
                
                <button 
                    @click="transferCall" 
                    class="control-btn transfer-btn">
                    🔄 Transfer
                </button>
            </div>

            <!-- Call Quality Indicator -->
            <div v-if="callStatus === 'answered'" class="quality-section">
                <h4>Call Quality</h4>
                <div class="quality-indicator">
                    <div class="quality-bars">
                        <div class="bar active"></div>
                        <div class="bar active"></div>
                        <div class="bar active"></div>
                        <div class="bar"></div>
                        <div class="bar"></div>
                    </div>
                    <span class="quality-text">Good</span>
                </div>
            </div>
        </div>
    `
};