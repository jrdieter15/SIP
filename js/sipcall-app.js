import { createApp } from 'vue';

createApp({
  data() {
    return { status: 'Ready' }
  },
  template: `<div><h3>SIP Call App</h3><p>Status: {{ status }}</p></div>`
}).mount('#sipcall-app');
