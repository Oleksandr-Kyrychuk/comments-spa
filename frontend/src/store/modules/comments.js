import axios from 'axios';
import { toRaw } from 'vue';

export default {
  namespaced: true,
  state: () => ({
    comments: [], // Гарантуємо порожній масив
    pagination: { previous: null, next: null },
    ordering: '-created_at',
    currentPage: 1,
  }),
  mutations: {
  SET_COMMENTS(state, comments) {
    const commentsArray = Array.isArray(comments) ? comments : [];
    state.comments = commentsArray.map(c => ({
      ...c,
      tempId: c.tempId || `tmp_${c.id || Date.now()}_${Math.random()}`,
      user: {
        username: c.user?.username || c.user_name || 'Анонім',
        email: c.user?.email || '',
        homepage: c.user?.homepage || '',
      },
      replies: c.replies || [],
      parent: c.parent || null,
      parent_username: c.parent_username || null,
    }));
  },
  ADD_COMMENT(state, comment) {
    state.comments.unshift({
      ...comment,
      tempId: comment.tempId || `tmp_${comment.id || Date.now()}_${Math.random()}`,
      replies: comment.replies || [],
    });
  },
  ADD_REPLY(state, { parentId, reply }) {
    const findComment = (comments, id) => {
      const rawComments = toRaw(comments); // знімаємо Proxy
      for (const c of rawComments) {
        if (c.id === id || c.tempId === id) return c;
        if (c.replies?.length) {
          const found = findComment(c.replies, id);
          if (found) return found;
        }
      }
      return null;
    };

    const parent = findComment(state.comments, parentId);
    if (parent) {
      parent.replies = [
        ...(parent.replies || []),
        {
          ...reply,
          tempId: reply.tempId || `tmp_${reply.id || Date.now()}_${Math.random()}`,
          replies: reply.replies || [],
        },
      ];
    }
  },
  UPDATE_COMMENT(state, { tempId, updatedComment }) {
    const updateComment = (comments) => {
      for (let i = 0; i < comments.length; i++) {
        if (comments[i].tempId === tempId) {
          comments[i] = { ...comments[i], ...updatedComment, tempId: comments[i].tempId };
          return true;
        }
        if (comments[i].replies?.length) {
          if (updateComment(comments[i].replies)) return true;
        }
      }
      return false;
    };
    updateComment(state.comments);
  },
},
  actions: {
    async fetchComments({ commit, state }, { baseUrl, page = 1 } = {}) {
      try {
        const apiUrl = baseUrl || 'http://localhost:8000/api';
        console.log('Fetching comments from:', `${apiUrl}/comments/`, 'with params:', { ordering: state.ordering, page });
        let allComments = [];
        let nextPage = page;

        // Завантажуємо всі сторінки коментарів
        while (nextPage) {
          const res = await axios.get(`${apiUrl}/comments/`, {
            params: { ordering: state.ordering, page: nextPage },
            withCredentials: true,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
          });

          console.log('API response:', res.data);
          console.log('Results:', res.data.results);
          console.log('Pagination:', { previous: res.data.previous, next: res.data.next });

          const normalizeReplies = (comment) => {
            console.log('Normalizing comment:', comment);
            comment.replies = comment.replies?.map(r => normalizeReplies(r)) || [];
            comment.user = {
              username: comment.user?.username || comment.user_name || 'Анонім',
              email: comment.user?.email || '',
              homepage: comment.user?.homepage || '',
            };
            return comment;
          };

          const comments = (res.data.results || []).map(normalizeReplies);
allComments = [...allComments, ...comments];

// Додай дебаг
console.log('All comments before commit:', allComments.map(c => ({
  id: c.id,
  tempId: c.tempId,
  parent: c.parent,
  text: c.text
})));

commit('SET_COMMENTS', allComments);
commit('SET_PAGINATION', { previous: res.data.previous, next: res.data.next });
commit('SET_CURRENT_PAGE', nextPage);

          nextPage = res.data.next ? nextPage + 1 : null;
        }
      } catch (err) {
        console.error('Fetch comments error:', err.response?.data || err.message);
        console.error('Status:', err.response?.status);
        console.error('Headers:', err.response?.headers);
      }
    },
  },
};