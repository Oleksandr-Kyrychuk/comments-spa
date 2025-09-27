import axios from 'axios';
import { toRaw } from 'vue';

const api = axios.create({
  baseURL: process.env.VUE_APP_API_BASE,
  withCredentials: true,
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
});

// Додаємо CSRF-токен до POST-запитів
api.interceptors.request.use(config => {
  if (config.method?.toLowerCase() === 'post') {
    const csrfToken = document.cookie.match(/csrftoken=([^;]+)/)?.[1];
    if (csrfToken) config.headers['X-CSRFToken'] = csrfToken;
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
    },
    SET_PAGINATION(state, pagination) {
      state.pagination = pagination;
    },
    SET_CURRENT_PAGE(state, page) {
      state.currentPage = page;
    },
    ADD_COMMENT(state, comment) {
      state.comments = [comment, ...state.comments];
    },
    ADD_REPLY(state, { parentId, reply }) {
      const findComment = (comments, id) => {
        const raw = toRaw(comments);
        for (const c of raw) {
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
          { ...reply, tempId: reply.tempId || `tmp_${Date.now()}_${Math.random()}`, replies: reply.replies || [] }
        ];
      }
    },
    UPDATE_COMMENT(state, { tempId, updatedComment }) {
      const findComment = comments => {
        const raw = toRaw(comments);
        for (const c of raw) {
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
      findComment(state.comments);
    },
    SET_WS_CONNECTED(state, connected) {
      state.wsConnected = connected;
    },
    SET_CAPTCHA(state, captcha) {
      state.captcha = captcha;
    },
  },
  actions: {
    async fetchCsrfToken() {
      await api.get(process.env.VUE_APP_CSRF_URL);
    },
    async fetchComments({ commit, state }, { page = 1 } = {}) {
      const res = await api.get('/comments/', { params: { ordering: state.ordering, page } });
      const normalize = comment => {
        comment.replies = comment.replies?.map(normalize) || [];
        comment.user = {
          username: comment.user?.username || comment.user_name || 'Анонім',
          email: comment.user?.email || '',
          homepage: comment.user?.homepage || '',
        };
        return comment;
      };
      const comments = (res.data.results || []).map(normalize);
      commit('SET_COMMENTS', comments);
      commit('SET_PAGINATION', { previous: res.data.previous, next: res.data.next });
      commit('SET_CURRENT_PAGE', page);
      return comments;
    },
    async createComment({ commit, dispatch }, { commentData, parentId = null }) {
      const tempId = `tmp_${Date.now()}_${Math.random()}`;
      const tempComment = { ...commentData, tempId, id: null, replies: [], created_at: new Date().toISOString() };

      if (parentId) commit('ADD_REPLY', { parentId, reply: tempComment });
      else commit('ADD_COMMENT', tempComment);

      const res = await api.post('/comments/', { ...commentData, parent: parentId });
      commit('UPDATE_COMMENT', { tempId, updatedComment: res.data.data });
      return res.data;
    },
    async fetchCaptcha({ commit }) {
      const res = await api.get(process.env.VUE_APP_CAPTCHA_URL);
      commit('SET_CAPTCHA', res.data);
      return res.data;
    },
    async connectWebSocket({ commit, dispatch }) {
      if (ws) ws.close();
      ws = new WebSocket(process.env.VUE_APP_WS_BASE);

      ws.onopen = () => commit('SET_WS_CONNECTED', true);
      ws.onmessage = e => {
        const data = JSON.parse(e.data);
        if (data.type === 'new_comment') dispatch('fetchComments', { page: 1 });
      };
      ws.onclose = () => {
        commit('SET_WS_CONNECTED', false);
        setTimeout(() => dispatch('connectWebSocket'), 5000);
      };
      ws.onerror = () => commit('SET_WS_CONNECTED', false);
    },
    changePage({ dispatch }, { page }) {
      dispatch('fetchComments', { page });
    },
  },
};
