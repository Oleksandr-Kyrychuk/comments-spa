import { createRouter, createWebHistory } from 'vue-router';
import CommentList from '../components/CommentList.vue';  // Створимо пізніше
import CommentForm from '../components/CommentForm.vue';  // Створимо пізніше

const routes = [
  { path: '/', name: 'Home', component: CommentList },
  { path: '/add', name: 'AddComment', component: CommentForm },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;