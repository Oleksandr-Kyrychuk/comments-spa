import axios from 'axios';
import { toRaw } from 'vue';

export default {
  namespaced: true,
  state: () => ({
    comments: [], // всі завантажені коментарі
    pagination: { previous: null, next: null },
    ordering: '-created_at',
    currentPage: 1,
  }),
  mutations: {
    SET_COMMENTS(state, comments) {
      state.comments = comments;
    },
    SET_PAGINATION(state, pagination) {
      state.pagination = pagination;
    },
    SET_CURRENT_PAGE(state, page) {
      state.currentPage = page;
    },
    ADD_COMMENT(state, comment) {
      // перевіряємо, чи коментар вже є (по id або tempId)
      const exists = state.comments.some(c => c.id === comment.id || c.tempId === comment.tempId);
      if (!exists) {
        state.comments = [comment, ...state.comments];
      }
    },
    ADD_REPLY(state, { parentId, reply }) {
      const findComment = (comments, id) => {
        const rawComments = toRaw(comments);
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
      } else {
        console.warn('Parent comment not found for parentId:', parentId);
      }
    },
    UPDATE_COMMENT(state, updatedComment) {
      const findAndUpdate = (comments) => {
        const rawComments = toRaw(comments);
        for (const c of rawComments) {
          if (c.id === updatedComment.id || c.tempId === updatedComment.tempId) {
            Object.assign(c, updatedComment);
            return true;
          }
          if (c.replies?.length) {
            if (findAndUpdate(c.replies)) return true;
          }
        }
        return false;
      };

      if (!findAndUpdate(state.comments)) {
        console.warn('Comment not found for update:', updatedComment);
      }
    },
  },
  actions: {
    async fetchComments({ commit, state }, { baseUrl, page = 1, ordering } = {}) {
      try {
        const apiUrl = baseUrl || 'http://localhost:8000/api';
        const res = await axios.get(`${apiUrl}/comments/`, {
          params: { ordering: ordering || state.ordering, page },
          withCredentials: true,
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });

        const normalizeReplies = (comment) => {
          comment.replies = comment.replies?.map(normalizeReplies) || [];
          comment.user = {
            username: comment.user?.username || comment.user_name || 'Анонім',
            email: comment.user?.email || '',
            homepage: comment.user?.homepage || '',
          };
          return comment;
        };

        const comments = (res.data.results || []).map(normalizeReplies);

        commit('SET_COMMENTS', comments);
        commit('SET_PAGINATION', { previous: res.data.previous, next: res.data.next });
        commit('SET_CURRENT_PAGE', page);

        return comments;
      } catch (err) {
        console.error('Fetch comments error:', err.response?.data || err.message);
        throw err;
      }
    },
    changePage({ dispatch }, { baseUrl, page }) {
      dispatch('fetchComments', { baseUrl, page });
    },
  },
};