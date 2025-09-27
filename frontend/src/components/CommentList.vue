<template>
  <div class="comment-list-container">
    <!-- Контролі: сортування + пагінація -->
    <div class="controls">
      <select v-model="ordering" @change="changeOrdering" class="form-control">
        <option value="-created_at">Newest first</option>
        <option value="created_at">Oldest first</option>
        <option value="user__username">By username</option>
        <option value="user__email">By email</option>
      </select>

      <div class="pagination">
        <button :disabled="!pagination.previous" @click="changePage('prev')" class="btn btn-secondary">Prev</button>
        <button :disabled="!pagination.next" @click="changePage('next')" class="btn btn-secondary">Next</button>
      </div>
    </div>

    <!-- Дебаг: відображення кількості коментарів -->
    <div>Завантажено коментарів: {{ comments.length }}</div>
    <div v-if="comments.length === 0" class="no-comments">Немає коментарів або помилка API. Перевірте консоль.</div>

    <!-- Таблиця коментарів -->
    <table class="comment-table">
      <thead>
        <tr>
          <th @click="changeOrdering('user__username')" class="sortable">Username</th>
          <th @click="changeOrdering('user__email')" class="sortable">Email</th>
          <th @click="changeOrdering('created_at')" class="sortable">Date</th>
          <th>Text</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="comment in comments" :key="comment.id || comment.tempId" class="comment-row">
          <td>{{ comment.user?.username || 'Анонім' }}</td>
          <td>
            <a v-if="comment.user?.email" :href="'mailto:' + comment.user.email">{{ comment.user.email }}</a>
          </td>
          <td>{{ formatDate(comment.created_at) }}</td>
          <td>
            <div v-html="comment.text"></div>
            <div v-if="comment.file">
              <a v-if="isTextFile(comment.file)" :href="getFileUrl(comment.file)" download>Download TXT</a>
              <img
                v-else
                :src="getFileUrl(comment.file)"
                @click="openLightbox(getFileUrl(comment.file))"
                class="comment-image"
              />
            </div>
            <button
              v-if="comment.id"
              @click="showReplyForm[comment.id || comment.tempId] = !showReplyForm[comment.id || comment.tempId]"
              class="btn btn-link"
            >
              Reply
            </button>

            <div v-if="showReplyForm[comment.id || comment.tempId]" class="reply-form">
              <CommentForm :parentId="comment.id" @submitted="handleCommentSubmitted" />
            </div>

            <!-- Вкладені коментарі -->
            <div v-if="comment.replies?.length" class="replies">
              <CommentItem
                v-for="reply in comment.replies"
                :key="reply.id || reply.tempId"
                :comment="reply"
                :level="1"
                @add-reply="handleAddReply"
              />
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Lightbox -->
    <EasyLightbox v-model:visible="visible" :imgs="[lightboxUrl]" />

    <!-- Форма нового коментаря -->
    <CommentForm @submitted="handleCommentSubmitted" />
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useStore } from 'vuex';
import CommentItem from './CommentItem.vue';
import CommentForm from './CommentForm.vue';
import EasyLightbox from 'vue-easy-lightbox';

const WS_BASE = process.env.VUE_APP_WS_BASE || 'ws://localhost:8000/ws/comments/';
const API_BASE = process.env.VUE_APP_API_BASE || 'http://localhost:8000/api';
const MEDIA_URL = process.env.VUE_APP_API_BASE ? `${process.env.VUE_APP_API_BASE}/media/` : 'http://localhost:8000/media/';

export default {
  components: { CommentItem, CommentForm, EasyLightbox },
  setup() {
    const store = useStore();
    const visible = ref(false);
    const lightboxUrl = ref('');
    const showReplyForm = ref({});

    // Синхронізація ordering з модулем
    const ordering = computed({
      get: () => store.state.comments.ordering,
      set: (val) => store.commit('comments/SET_ORDERING', val),
    });

    // Доступ до comments через модуль
    const comments = computed(() => {
      const data = store.state.comments?.comments || [];
      console.log('Computed comments:', data); // Дебаг
      return data;
    });

    // Пагінація з модуля
    const pagination = computed(() => store.state.comments?.pagination || { next: null, previous: null });

    let ws = null;
    const connectWebSocket = () => {
      ws = new WebSocket(WS_BASE);
      ws.onopen = () => console.log('WebSocket connected');
      ws.onmessage = event => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data); // Лог для дебагу
        if (data.type === 'new_comment') handleIncomingComment(data.comment);
      };
      ws.onclose = () => {
        console.log('WebSocket closed, reconnecting...');
        setTimeout(connectWebSocket, 1000);
      };
      ws.onerror = err => console.error('WebSocket error:', err);
    };

    const handleIncomingComment = (newComment) => {
  console.log('Handling incoming comment:', newComment);
  console.log('Comment ID:', newComment.id, 'Parent:', newComment.parent);
  console.log('Existing comments:', store.state.comments.comments);

  // Ініціалізуємо comments, якщо він ще не існує
  if (!store.state.comments?.comments) {
    store.commit('comments/SET_COMMENTS', []);
  }

  const commentsArray = store.state.comments.comments || [];
  const existing = commentsArray.find(
    c => c.tempId === newComment.tempId || c.id === newComment.id
  );

  if (existing) {
    console.log('Updating existing comment with tempId:', existing.tempId, 'to ID:', newComment.id);
    store.commit('comments/UPDATE_COMMENT', { tempId: newComment.tempId, updatedComment: newComment });
  } else {
    console.log('Adding new comment:', newComment);
    if (newComment.parent) {
      store.commit('comments/ADD_REPLY', { parentId: newComment.parent, reply: newComment });
    } else {
      store.commit('comments/ADD_COMMENT', newComment);
    }
  }
};

    const handleCommentSubmitted = ({ comment, parentId }) => {
      console.log('Comment submitted:', comment, 'Parent:', parentId);
      if (parentId) {
        store.commit('comments/ADD_REPLY', { parentId, reply: comment });
      } else {
        store.commit('comments/ADD_COMMENT', comment);
      }
    };

    const changePage = dir => {
      const current = store.state.comments.currentPage || 1;
      const page = dir === 'next' ? current + 1 : current - 1;
      store.dispatch('comments/fetchComments', { baseUrl: API_BASE, page });
    };

    const changeOrdering = field => {
      let newOrder = field || ordering.value;
      if (ordering.value === field) newOrder = field.startsWith('-') ? field.slice(1) : `-${field}`;
      ordering.value = newOrder; // Автоматично через computed setter
      store.dispatch('comments/fetchComments', { baseUrl: API_BASE });
    };

    const openLightbox = url => { lightboxUrl.value = url; visible.value = true; };
    const isTextFile = filePath => filePath?.endsWith('.txt') || false;
    const getFileUrl = filePath => filePath ? (filePath.startsWith(MEDIA_URL) ? filePath : MEDIA_URL + filePath) : '';
    const formatDate = dateStr => new Date(dateStr).toLocaleString();

    onMounted(() => {
      console.log('Fetching comments on mount');
      store.dispatch('comments/fetchComments', { baseUrl: API_BASE });
      connectWebSocket();
    });

    onUnmounted(() => { if (ws) ws.close(); });

    return {
      comments,
      pagination,
      ordering,
      changePage,
      changeOrdering,
      handleAddReply: ({ parentId, reply }) => store.commit('comments/ADD_REPLY', { parentId, reply }),
      handleCommentSubmitted,
      visible,
      lightboxUrl,
      openLightbox,
      isTextFile,
      getFileUrl,
      formatDate,
      showReplyForm,
    };
  },
};
</script>

<style scoped>
.comment-list-container { padding: 20px; max-width: 1200px; margin: 0 auto; }
.controls { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.form-control { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
.pagination { display: flex; gap: 10px; }
.btn { padding: 8px 16px; border: none; border-radius: 4px; background-color: #007bff; color: white; cursor: pointer; }
.btn:disabled { background-color: #ccc; cursor: not-allowed; }
.btn-secondary { background-color: #6c757d; }
.comment-table { width: 100%; border-collapse: collapse; margin-bottom: 20px; background-color: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.comment-table th, .comment-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
.comment-table th { background-color: #f8f9fa; font-weight: bold; color: #333; cursor: pointer; }
.comment-row:hover { background-color: #f1f3f5; }
.comment-image { max-width: 320px; cursor: pointer; margin-top: 10px; }
.reply-form { margin-top: 10px; }
.replies { padding-left: 20px; border-left: 3px solid #ccc; margin-top: 10px; }
.no-comments { padding: 10px; color: red; }
@media (max-width: 768px) {
  .comment-table { display: block; overflow-x: auto; white-space: nowrap; }
  .comment-table th, .comment-table td { min-width: 100px; }
  .comment-table td:nth-child(4) { min-width: 300px; }
}
</style>