<template>
  <div>
    <select v-model="ordering" @change="changeOrdering">
      <option value="-created_at">Newest first</option>
      <option value="created_at">Oldest first</option>
      <option value="user__username">By username</option>
      <option value="user__email">By email</option>
    </select>

    <button :disabled="!pagination.previous" @click="changePage('prev')">Prev</button>
    <button :disabled="!pagination.next" @click="changePage('next')">Next</button>

    <div class="comment-thread">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        @add-reply="handleAddReply"
      />
    </div>

    <CommentForm @submitted="handleCommentSubmitted" />
  </div>
</template>

<script>
import { computed, onMounted, onUnmounted } from 'vue';
import { useStore } from 'vuex';
import CommentItem from './CommentItem.vue';
import CommentForm from './CommentForm.vue';

const WS_BASE = process.env.VUE_APP_WS_BASE || 'ws://django:8000/ws/comments/'; // Змінено на ім'я сервісу бекенду
const API_BASE = process.env.VUE_APP_API_BASE || 'http://localhost:8000';

export default {
  components: { CommentItem, CommentForm },
  setup() {
    const store = useStore();

    const comments = computed(() => store.state.comments);
    const pagination = computed(() => store.state.pagination || { previous: null, next: null }); // Додано fallback
    const ordering = computed({
      get: () => store.state.ordering,
      set: (val) => store.commit('SET_ORDERING', val),
    });

    let ws = null;

    const connectWebSocket = () => {
      ws = new WebSocket(WS_BASE);
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data); // Дебаг
        if (data.type === 'new_comment') {
          console.log('New comment received:', data.comment);
          if (data.comment.parent) {
            store.commit('ADD_REPLY', {
              parentId: data.comment.parent,
              reply: data.comment,
            });
          } else {
            store.commit('ADD_COMMENT', data.comment);
          }
        }
      };
      ws.onclose = () => {
        console.log('WebSocket closed, attempting to reconnect...');
        setTimeout(connectWebSocket, 1000); // Повторна спроба підключення через 1 секунду
      };
      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
      };
    };

    const handleAddReply = ({ parentId, reply }) => {
      store.commit('ADD_REPLY', { parentId, reply });
    };

    const handleCommentSubmitted = (newComment) => {
      if (newComment.parentId) {
        store.commit('ADD_REPLY', {
          parentId: newComment.parentId,
          reply: newComment.comment,
        });
      } else {
        store.commit('ADD_COMMENT', newComment.comment);
      }
    };

    onMounted(() => {
  // Завантажуємо коментарі через API
  store.dispatch('comments/fetchComments', { baseUrl: API_BASE })
    .then(() => {
      console.log('Comments loaded:', store.state.comments);
    })
    .catch(err => {
      console.error('Failed to fetch comments:', err);
    });

  // Підключаємо WebSocket
  connectWebSocket();
});

    onUnmounted(() => {
      if (ws) ws.close();
    });

    const changePage = (dir) => {
      const current = store.state.currentPage || 1; // Додано fallback для currentPage
      store.dispatch('fetchComments', {
        baseUrl: API_BASE,
        page: dir === 'next' ? current + 1 : current - 1,
      });
    };

    const changeOrdering = () => {
      store.dispatch('fetchComments', { baseUrl: API_BASE });
    };

    return {
      comments,
      pagination,
      ordering,
      changePage,
      changeOrdering,
      handleAddReply,
      handleCommentSubmitted,
    };
  },
};
</script>

<style scoped>
.comment-thread {
  margin-top: 20px;
}
</style>