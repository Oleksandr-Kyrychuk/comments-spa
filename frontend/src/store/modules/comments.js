import axios from 'axios';
import { toRaw } from 'vue';

const api = axios.create({
  baseURL: process.env.VUE_APP_API_BASE,
  withCredentials: true,
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
  },
});

// Додаємо CSRF-токен до POST-запитів
api.interceptors.request.use(config => {
  if (config.method.toLowerCase() === 'post') {
    const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    } else {
      console.warn('CSRF token not found in cookies');
    }
  }
  return config;
});

let ws = null;

export default {
  namespaced: true,
  state: () => ({
    comments: [],
    pagination: { previous: null, next: null },
    ordering: '-created_at',
    currentPage: 1,
    wsConnected: false,
    captcha: null,
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
    SET_WS_CONNECTED(state, connected) {
      state.wsConnected = connected;
      console.log('WebSocket connected:', connected);
    },
    SET_CAPTCHA(state, captcha) {
      state.captcha = captcha;
      console.log('SET_CAPTCHA:', captcha);
    },
  },
  actions: {
    async fetchCsrfToken({ commit }) {
      try {
        console.log('Fetching CSRF token from:', process.env.VUE_APP_CSRF_URL);
        await api.get(process.env.VUE_APP_CSRF_URL);
        console.log('CSRF token fetched successfully');
      } catch (err) {
        console.error('Error fetching CSRF token:', err.response?.data || err.message);
        throw err;
      }
    },
    async fetchComments({ commit, state }, { page = 1 } = {}) {
      try {
        console.log('Fetching comments from:', `${process.env.VUE_APP_API_BASE}/comments/`, 'with params:', { ordering: state.ordering, page });

        const res = await api.get('/comments/', {
          params: { ordering: state.ordering, page },
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

        commit('SET_COMMENTS', comments);
        commit('SET_PAGINATION', { previous: res.data.previous, next: res.data.next });
        commit('SET_CURRENT_PAGE', page);

        return comments;
      } catch (err) {
        console.error('Fetch comments error:', err.response?.data || err.message);
        console.error('Status:', err.response?.status);
        console.error('Headers:', err.response?.headers);
        throw err;
      }
    },
    async createComment({ commit, dispatch }, { commentData, parentId = null }) {
      try {
        const tempId = `tmp_${Date.now()}_${Math.random()}`;
        const tempComment = {
          ...commentData,
          tempId,
          id: null,
          replies: [],
          created_at: new Date().toISOString(),
        };

        if (parentId) {
          commit('ADD_REPLY', { parentId, reply: tempComment });
        } else {
          commit('ADD_COMMENT', tempComment);
        }

        console.log('Creating comment with data:', { ...commentData, parent: parentId });
        const res = await api.post('/comments/', { ...commentData, parent: parentId });
        console.log('Comment created:', res.data);

        commit('UPDATE_COMMENT', { tempId, updatedComment: res.data.data });
        return res.data;
      } catch (err) {
        console.error('Create comment error:', err.response?.data || err.message);
        throw err;
      }
    },
    async fetchCaptcha({ commit }) {
      try {
        console.log('Fetching CAPTCHA from:', process.env.VUE_APP_CAPTCHA_URL);
        const res = await api.get(process.env.VUE_APP_CAPTCHA_URL);
        console.log('CAPTCHA fetched:', res.data);
        commit('SET_CAPTCHA', res.data);
        return res.data;
      } catch (err) {
        console.error('Fetch CAPTCHA error:', err.response?.data || err.message);
        throw err;
      }
    },
    async connectWebSocket({ commit, dispatch }) {
      if (ws) {
        ws.close();
      }
      ws = new WebSocket(process.env.VUE_APP_WS_BASE);
      ws.onopen = () => {
        console.log('WebSocket connected to:', process.env.VUE_APP_WS_BASE);
        commit('SET_WS_CONNECTED', true);
      };
      ws.onmessage = (event) => {
        console.log('WebSocket message received:', event.data);
        const data = JSON.parse(event.data);
        if (data.type === 'new_comment') {
          dispatch('fetchComments', { page: 1 });
        }
      };
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        commit('SET_WS_CONNECTED', false);
        setTimeout(() => dispatch('connectWebSocket'), 5000);
      };
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        commit('SET_WS_CONNECTED', false);
      };
    },
    changePage({ dispatch }, { page }) {
      console.log('Changing page to:', page);
      dispatch('fetchComments', { page });
    },
  },
};