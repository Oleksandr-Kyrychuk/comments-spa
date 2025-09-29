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
      console.log('SET_COMMENTS:', comments.map(c => ({ id: c.id, text: c.text })));
    },
    SET_PAGINATION(state, pagination) {
      state.pagination = pagination;
      console.log('SET_PAGINATION:', pagination);
    },
    SET_CURRENT_PAGE(state, page) {
      state.currentPage = page;
      console.log('SET_CURRENT_PAGE:', page);
    },
    ADD_COMMENT(state, comment) {
      // Перевіряємо, чи коментар уже є (по id або tempId)
      const exists = state.comments.some(c => c.id === comment.id || c.tempId === comment.tempId);
      if (!exists) {
        state.comments = [comment, ...state.comments];
        console.log('ADD_COMMENT:', { id: comment.id, text: comment.text });
      } else {
        console.log('Comment already exists, skipping:', comment);
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
        console.log('ADD_REPLY:', { parentId, reply: { id: reply.id, text: reply.text } });
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
            console.log('UPDATE_COMMENT:', { id: updatedComment.id, text: updatedComment.text });
            return true;
          }
          if (c.replies?.length) {
            if (findAndUpdate(c.replies)) return true;
          }
        }
        return false;
      };

      if (!findAndUpdate(state.comments)) {
        // Якщо коментар не знайдено, додаємо як новий
        state.comments = [updatedComment, ...state.comments];
        console.log('UPDATE_COMMENT: Added as new comment:', { id: updatedComment.id, text: updatedComment.text });
      }
    },
  },
  actions: {
    async fetchComments({ commit, state }, { baseUrl, page = 1, ordering } = {}) {
      try {
        const apiUrl = baseUrl || 'http://localhost:8000/api';
        console.log('Fetching comments from:', `${apiUrl}/comments/`, 'with params:', { ordering: ordering || state.ordering, page });
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
        console.log('Fetched comments:', comments.map(c => ({ id: c.id, text: c.text })));

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
      console.log('Changing page to:', page);
      dispatch('fetchComments', { baseUrl, page });
    },
  },
};