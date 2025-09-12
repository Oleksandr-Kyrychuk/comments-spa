<template>
  <div>
    <select v-model="ordering" @change="changeOrdering">
      <option value="-created_at">Newest first</option>
      <option value="created_at">Oldest first</option>
      <option value="user_name">By user name</option>
      <option value="email">By email</option>
    </select>
    <table>
      <thead><tr><th>User</th><th>Email</th><th>Text</th><th>File</th><th>Date</th></tr></thead>
      <tbody>
        <CommentItem v-for="comment in comments" :key="comment.id" :comment="comment" />
      </tbody>
    </table>
    <button :disabled="!pagination.previous" @click="changePage('prev')">Prev</button>
    <button :disabled="!pagination.next" @click="changePage('next')">Next</button>
  </div>
</template>

<script>
import { computed, onMounted } from 'vue';
import { useStore } from 'vuex';
import CommentItem from './CommentItem.vue';

export default {
  components: { CommentItem },
  setup() {
    const store = useStore();
    const comments = computed(() => store.state.comments);
    const pagination = computed(() => store.state.pagination);
    const ordering = computed({
      get: () => store.state.ordering,
      set: (val) => store.commit('SET_ORDERING', val),
    });

    const WS_BASE = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') + window.location.host + '/ws/comments/';

    onMounted(() => {
  store.dispatch('fetchComments');

  const ws = new WebSocket(WS_BASE);
  ws.onmessage = (event) => {
    console.log('New WS message:', event.data);
  };
});

    const changePage = (dir) => {
      const current = store.state.currentPage;
      store.dispatch('fetchComments', dir === 'next' ? current + 1 : current - 1);
    };

    const changeOrdering = () => {
      store.dispatch('fetchComments');
    };

    return { comments, pagination, ordering, changePage, changeOrdering };
  },
};
</script>
