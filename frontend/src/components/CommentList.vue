<template>
  <div>
    <select v-model="ordering" @change="changeOrdering">
      <option value="-created_at">Newest first</option>
      <option value="created_at">Oldest first</option>
      <option value="user_name">By user name</option>
      <option value="email">By email</option>
    </select>

    <button :disabled="!pagination.previous" @click="changePage('prev')">Prev</button>
    <button :disabled="!pagination.next" @click="changePage('next')">Next</button>

    <div class="comment-thread">
      <CommentItem v-for="comment in comments" :key="comment.id" :comment="comment" @add-reply="handleAddReply" />
    </div>

    <CommentForm />
  </div>
</template>

<script>
import { computed, onMounted, onUnmounted } from 'vue';
import { useStore } from 'vuex';
import CommentItem from './CommentItem.vue';
import CommentForm from './CommentForm.vue';

export default {
  components: { CommentItem, CommentForm },
  setup() {
    const store = useStore();

    const comments = computed(() => store.state.comments);
    const pagination = computed(() => store.state.pagination);
    const ordering = computed({
      get: () => store.state.ordering,
      set: (val) => store.commit('SET_ORDERING', val),
    });

    const WS_BASE = 'ws://localhost:8000/ws/comments/';
    let ws = null;

    const connectWebSocket = () => {
      ws = new WebSocket(WS_BASE);
      ws.onopen = () => console.log('WebSocket connected');
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
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
      ws.onclose = () => console.log('WebSocket closed');
      ws.onerror = (err) => console.error('WebSocket error:', err);
    };

    const handleAddReply = ({ parentId, reply }) => {
      // Комітить reply у store
      store.commit('ADD_REPLY', { parentId, reply });
    };

    onMounted(() => {
      store.dispatch('fetchComments').then(() => {
        console.log('Comments loaded:', store.state.comments);
      });
      connectWebSocket();
    });

    onUnmounted(() => {
      if (ws) ws.close();
    });

    const changePage = (dir) => {
      const current = store.state.currentPage;
      store.dispatch('fetchComments', dir === 'next' ? current + 1 : current - 1);
    };

    const changeOrdering = () => {
      store.dispatch('fetchComments');
    };

    return { comments, pagination, ordering, changePage, changeOrdering, handleAddReply };
  },
};
</script>

<style scoped>
.comment-thread { margin-top: 20px; }
</style>