/**
 * Dialpad Section Component
 * Handles number input, dialpad, and call actions
 */

export default {
    name: 'DialpadSection',
    
    props: {
        destinationNumber: {
            type: String,
            default: ''
        },
        isCallActive: {
            type: Boolean,
            default: false
        },
        loading: {
            type: Boolean,
            default: false
        },
        privacyMode: {
            type: Boolean,
            default: false
        }
    },
    
    emits: [
        'update:destinationNumber',
        'update:privacyMode',
        'start-call',
        'end-call',
        'add-digit',
        'clear-number',
        'delete-digit'
    ],
    
    data() {
        return {
            isDialpadVisible: true
        };
    },
    
    computed: {
        localDestinationNumber: {
            get() {
                return this.destinationNumber;
            },
            set(value) {
                this.$emit('update:destinationNumber', value);
            }
        },
        
        localPrivacyMode: {
            get() {
                return this.privacyMode;
            },
            set(value) {
                this.$emit('update:privacyMode', value);
            }
        }
    },
    
    methods: {
        addDigit(digit) {
            this.$emit('add-digit', digit);
        },
        
        clearNumber() {
            this.$emit('clear-number');
        },
        
        deleteDigit() {
            this.$emit('delete-digit');
        },
        
        startCall() {
            this.$emit('start-call');
        },
        
        endCall() {
            this.$emit('end-call');
        },
        
        handleKeyPress(event) {
            if (event.key === 'Enter') {
                this.startCall();
            } else if (event.key === 'Backspace') {
                this.deleteDigit();
            } else if (/[0-9*#]/.test(event.key)) {
                this.addDigit(event.key);
            }
        }
    },
    
    template: `
        <div class="dialpad-section">
            <h3>Make a Call</h3>
            
            <!-- Number Input -->
            <div class="number-input">
                <input 
                    v-model="localDestinationNumber" 
                    type="tel" 
                    placeholder="Enter phone number"
                    class="phone-input"
                    :disabled="isCallActive"
                    @keydown="handleKeyPress"
                />
                <button 
                    v-if="localDestinationNumber" 
                    @click="clearNumber"
                    class="clear-btn"
                    :disabled="isCallActive">
                    Clear
                </button>
            </div>

            <!-- Dialpad Grid -->
            <div v-if="isDialpadVisible" class="dialpad-grid">
                <button 
                    v-for="digit in ['1','2','3','4','5','6','7','8','9','*','0','#']" 
                    :key="digit"
                    @click="addDigit(digit)"
                    class="dialpad-button"
                    :disabled="isCallActive">
                    {{ digit }}
                </button>
            </div>

            <!-- Call Actions -->
            <div class="call-actions">
                <button 
                    v-if="!isCallActive" 
                    @click="startCall" 
                    class="start-call-btn"
                    :disabled="!localDestinationNumber.trim() || loading">
                    {{ loading ? 'Connecting...' : 'Start Call' }}
                </button>
                
                <button 
                    v-if="isCallActive" 
                    @click="endCall" 
                    class="end-call-btn"
                    :disabled="loading">
                    {{ loading ? 'Ending...' : 'End Call' }}
                </button>
            </div>

            <!-- Privacy Mode Toggle -->
            <div class="privacy-section">
                <h4>Privacy Settings</h4>
                <div class="privacy-toggle">
                    <label class="toggle-label">
                        <input 
                            type="checkbox" 
                            v-model="localPrivacyMode"
                            :disabled="isCallActive">
                        <span class="toggle-slider"></span>
                        Ephemeral Session (no call logging)
                    </label>
                </div>
            </div>
        </div>
    `
};