<template>
  <div class="container mx-auto p-6 max-w-4xl">
    <h2 class="text-2xl font-bold mb-4">Коментарі</h2>
    <CommentForm @submitted="handleCommentSubmitted" />
    <div class="flex items-center mb-4">
      <label class="mr-2">Сортувати за:</label>
      <select v-model="ordering" @change="fetchComments" class="border rounded p-2">
        <option value="-created_at">Спочатку нові</option>
        <option value="created_at">Спочатку старі</option>
        <option value="user__username">Ім'я користувача</option>
        <option value="user__email">Email</option>
      </select>
    </div>
    <div v-if="comments.length">
      <CommentItem
        v-for="comment in comments"
        :key="comment.id || comment.tempId"
        :comment="comment"
        :level="1"
        @add-reply="handleCommentSubmitted"
      />
    </div>
    <div v-else>
      <p class="text-red-500">Коментарів поки немає.</p>
    </div>
    <div class="flex justify-between mt-4">
      <button
        :disabled="!pagination.previous"
        @click="changePage(currentPage - 1)"
        class="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
      >
        Попередня
      </button>
      <span>Сторінка {{ currentPage }}</span>
      <button
        :disabled="!pagination.next"
        @click="changePage(currentPage + 1)"
        class="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
      >
        Наступна
      </button>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { useStore } from 'vuex';
import CommentForm from './CommentForm.vue';
import CommentItem from './CommentItem.vue';

const API_BASE = process.env.VUE_APP_API_BASE || '/api';

export default {
  components: { CommentForm, CommentItem },
  setup() {
    const store = useStore();
    const ordering = ref('-created_at');
    const ws = ref(null);
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;
    const reconnectInterval = 3000;
    let pingInterval = null;

    const comments = computed(() => store.state.comments?.comments || []);
    const pagination = computed(() => store.state.comments?.pagination || { previous: null, next: null });
    const currentPage = computed(() => store.state.comments?.currentPage || 1);
    const isWebSocketConnected = computed(() => ws.value && ws.value.readyState === WebSocket.OPEN);

    // Спостерігаємо за змінами в comments
    watch(comments, (newComments) => {
      console.log('Comments updated:', newComments.map(c => ({ id: c.id, text: c.text })));
    }, { deep: true });

    const fetchComments = async () => {
      console.log('Fetching comments for page:', currentPage.value, 'with ordering:', ordering.value);
      await store.dispatch('comments/fetchComments', {
        baseUrl: API_BASE,
        page: currentPage.value,
        ordering: ordering.value,
      });
    };

    const changePage = async (page) => {
      console.log('Changing page to:', page);
      await store.dispatch('comments/changePage', {
        baseUrl: API_BASE,
        page,
      });
    };

    const handleCommentSubmitted = ({ parentId, comment }) => {
      console.log('Comment submitted:', comment, 'Parent:', parentId);
      if (parentId) {
        store.commit('comments/ADD_REPLY', { parentId, reply: comment });
        // Оновлюємо список для відображення відповідей
        fetchComments();
      } else {
        const existing = store.state.comments.comments.find(c => c.id === comment.id || c.tempId === comment.tempId);
        if (!existing) {
          store.commit('comments/ADD_COMMENT', comment);
          fetchComments();
        } else {
          console.log('Comment already exists, skipping:', comment);
        }
      }
      if (!ws.value || ws.value.readyState === WebSocket.CLOSED || ws.value.readyState === WebSocket.CLOSING) {
        console.log('WebSocket is closed or closing, attempting to reconnect');
        connectWebSocket();
      }
    };

    const handleIncomingComment = (newComment) => {
      console.log('Received WebSocket comment:', JSON.stringify(newComment, null, 2));
      console.log('Comment ID:', newComment.id, 'Parent:', newComment.parent);
      console.log('Existing comments:', store.state.comments.comments);

      if (!store.state.comments?.comments) {
        store.commit('comments/SET_COMMENTS', []);
      }

      const commentsArray = store.state.comments.comments || [];
      const existing = commentsArray.find(
        c => c.tempId === newComment.tempId || c.id === newComment.id
      );

      if (existing) {
        console.log('Updating existing comment with tempId:', existing.tempId, 'to ID:', newComment.id);
        store.commit('comments/UPDATE_COMMENT', newComment);
        fetchComments(); // Оновлюємо список для синхронізації
      } else {
        console.log('Adding new comment:', newComment);
        if (newComment.parent) {
          store.commit('comments/ADD_REPLY', { parentId: newComment.parent, reply: newComment });
          fetchComments(); // Оновлюємо список для відображення відповідей
        } else {
          store.commit('comments/ADD_COMMENT', newComment);
          fetchComments(); // Оновлюємо список для нових коментарів
        }
      }
    };

    const connectWebSocket = () => {
      let wsUrl;
      if (location.hostname === 'localhost' || location.hostname === '127.0.0.1') {
        wsUrl = 'ws://localhost:8000/ws/comments/';
      } else {
        wsUrl = 'wss://' + location.host + '/ws/comments/';
      }
      console.log('Connecting to WebSocket:', wsUrl);
      ws.value = new WebSocket(wsUrl);

      ws.value.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts = 0;
        pingInterval = setInterval(() => {
          if (ws.value && ws.value.readyState === WebSocket.OPEN) {
            ws.value.send(JSON.stringify({ type: 'ping' }));
            console.log('Sent WebSocket ping');
          }
        }, 30000);
      };

      ws.value.onmessage = (event) => {
        console.log('Raw WebSocket message:', event.data);
        let data;
        try {
          data = JSON.parse(event.data);
          console.log('Parsed WebSocket message:', JSON.stringify(data, null, 2));
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
          return;
        }

        if (data.type === 'new_comment') {
          handleIncomingComment(data.comment);
        } else if (data.id && data.text && data.created_at) {
          console.log('Treating message as direct comment:', data);
          handleIncomingComment(data);
        } else if (data.type === 'pong') {
          console.log('Received WebSocket pong');
        } else {
          console.warn('Unknown WebSocket message format:', data);
        }
      };

      ws.value.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.value.onclose = (event) => {
        console.log('WebSocket disconnected. Code:', event.code, 'Reason:', event.reason);
        clearInterval(pingInterval);
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++;
          console.log(`Reconnecting WebSocket, attempt ${reconnectAttempts}`);
          setTimeout(connectWebSocket, reconnectInterval);
        } else {
          console.error('Max WebSocket reconnect attempts reached');
          const pollInterval = setInterval(fetchComments, 30000);
          onUnmounted(() => clearInterval(pollInterval));
        }
      };
    };

    onMounted(() => {
      console.log('CommentList mounted');
      fetchComments();
      connectWebSocket();
      const pollInterval = setInterval(() => {
        if (!isWebSocketConnected.value) {
          console.log('WebSocket is not connected, polling comments');
          fetchComments();
        }
      }, 30000);
      return () => clearInterval(pollInterval);
    });

    onUnmounted(() => {
      if (ws.value) {
        clearInterval(pingInterval);
        ws.value.close();
        console.log('WebSocket closed');
      }
    });

    return {
      comments,
      ordering,
      pagination,
      currentPage,
      fetchComments,
      changePage,
      handleCommentSubmitted,
    };
  },
};
</script>

<style scoped>
</style>