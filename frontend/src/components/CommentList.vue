<template>
  <div class="comment-list">
    <h2>Comments</h2>
    <CommentForm @submitted="handleCommentSubmitted" />
    <div class="sort-panel">
      <label>Sort by:</label>
      <select v-model="ordering" @change="fetchComments">
        <option value="-created_at">Newest first</option>
        <option value="created_at">Oldest first</option>
        <option value="user__username">Username</option>
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
      <p>No comments yet.</p>
    </div>
    <div class="pagination">
      <button
        :disabled="!pagination.previous"
        @click="changePage(currentPage - 1)"
      >
        Previous
      </button>
      <span>Page {{ currentPage }}</span>
      <button
        :disabled="!pagination.next"
        @click="changePage(currentPage + 1)"
      >
        Next
      </button>
    </div>
  </div>
</template>

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

      const wsUrl = (API_BASE.startsWith('http') ? API_BASE.replace(/^https?/, 'wss') : 'wss://' + location.host + API_BASE) + '/ws/comments/';
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