import axios from 'axios';
import { toRaw } from 'vue';

export default {
  namespaced: true,
  state: () => ({
    comments: [],
    pagination: { previous: null, next: null },
    ordering: '-created_at',
    currentPage: 1,
  }),
  mutations: {
    SET_COMMENTS(state, comments) {
      state.comments = comments;
      console.log('SET_COMMENTS:', comments.map(c => ({ id: c.id, text: c.text, replies: c.replies.map(r => r.id) })));
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
      console.log('Adding comment:', comment);
      state.comments = [comment, ...state.comments];
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

      console.log('Adding reply with parentId:', parentId, 'Reply:', reply);
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
        console.log('Parent found, updated replies:', parent.replies);
      } else {
        console.error('Parent comment not found for parentId:', parentId);
      }
    },
    UPDATE_COMMENT(state, { tempId, updatedComment }) {
      console.log('Updating comment with tempId:', tempId, 'to:', updatedComment);
      const findComment = (comments) => {
        const rawComments = toRaw(comments);
        for (const c of rawComments) {
          if (c.tempId === tempId) {
            Object.assign(c, updatedComment);
            return true;
          }
          if (c.replies?.length) {
            if (findComment(c.replies)) return true;
          }
        }
        return false;
      };

      if (!findComment(state.comments)) {
        console.error('Comment with tempId not found:', tempId);
      }
    },
  },
  actions: {
    async fetchComments({ commit, state }, { baseUrl, page = 1 } = {}) {
      try {
        const apiUrl = baseUrl || 'http://localhost:8000/api';
        console.log('Fetching comments from:', `${apiUrl}/comments/`, 'with params:', { ordering: state.ordering, page });

        const res = await axios.get(`${apiUrl}/comments/`, {
          params: { ordering: state.ordering, page },
          withCredentials: true,
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });

        console.log('API response:', res.data);
        console.log('Results:', res.data.results);
        console.log('Replies for each comment:', res.data.results.map(c => ({ id: c.id, replies: c.replies.map(r => r.id) })));

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
        console.log('Comments for current page:', comments.map(c => ({ id: c.id, text: c.text, replies: c.replies.map(r => r.id) })));

        commit('SET_COMMENTS', comments); // Зберігаємо лише коментарі поточної сторінки
        commit('SET_PAGINATION', { previous: res.data.previous, next: res.data.next });
        commit('SET_CURRENT_PAGE', page);

        return comments; // Повертаємо коментарі для використання в компоненті
      } catch (err) {
        console.error('Fetch comments error:', err.response?.data || err.message);
        console.error('Status:', err.response?.status);
        console.error('Headers:', err.response?.headers);
        throw err;
      }
    },
    changePage({ dispatch }, { baseUrl, page }) {
  console.log('Changing page to:', page);
  dispatch('fetchComments', { baseUrl, page });
},
  },
};