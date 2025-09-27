import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';

const app = createApp(App);

// Отримуємо CSRF-токен і підключаємо WebSocket
store.dispatch('comments/fetchCsrfToken').then(() => {
  console.log('App initialized with CSRF token');
  store.dispatch('comments/connectWebSocket');
  app.use(store).use(router).mount('#app');
}).catch(err => {
  console.error('Failed to initialize CSRF token:', err);
  app.use(store).use(router).mount('#app');
});