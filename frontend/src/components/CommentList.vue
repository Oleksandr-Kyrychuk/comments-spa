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
</template>>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue';
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

    const comments = computed(() => store.state.comments?.comments || []);
    const pagination = computed(() => store.state.comments?.pagination || { previous: null, next: null });
    const currentPage = computed(() => store.state.comments?.currentPage || 1);

    const fetchComments = async () => {
      console.log('Fetching comments for page:', currentPage.value);
      await store.dispatch('comments/fetchComments', {
        baseUrl: API_BASE,
        page: currentPage.value,
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
      } else {
        store.commit('comments/ADD_COMMENT', comment);
      }
    };

    const handleIncomingComment = (newComment) => {
      console.log('Handling incoming comment:', newComment);
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

    onMounted(() => {
      console.log('CommentList mounted');
      fetchComments();

const wsUrl = 'wss://' + location.host + '/api/ws/comments/';
      console.log('Connecting to WebSocket:', wsUrl);
      ws.value = new WebSocket(wsUrl);

      ws.value.onopen = () => console.log('WebSocket connected');
      ws.value.onmessage = event => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message received:', data);
        console.log('Comment ID:', data.comment?.id, 'Parent:', data.comment?.parent);
        if (data.type === 'new_comment') handleIncomingComment(data.comment);
      };
      ws.value.onerror = error => console.error('WebSocket error:', error);
      ws.value.onclose = () => console.log('WebSocket disconnected');
    });

    onUnmounted(() => {
      if (ws.value) {
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