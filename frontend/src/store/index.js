// store/index.js
import { createStore } from 'vuex';
import axios from 'axios';
import createPersistedState from 'vuex-persistedstate';

const API_BASE = process.env.VUE_APP_API_BASE || 'http://localhost:8000/api';

export default createStore({
  plugins: [createPersistedState()],
  state: {
    comments: [],
    pagination: { next: null, previous: null, count: 0 },
    currentPage: 1,
    ordering: '-created_at',
  },
  mutations: {
    SET_COMMENTS(state, comments) {
      state.comments = comments.map(comment => ({
        ...comment,
        replies: comment.replies || [],
      }));
    },
    ADD_COMMENT(state, comment) {
      state.comments.unshift({ ...comment, replies: comment.replies || [] });
    },
    ADD_REPLY(state, { parentId, reply }) {
      const findAndAddReply = (comments) => {
        for (let comment of comments) {
          if (comment.id === parentId) {
            comment.replies = comment.replies || [];
            comment.replies.push({ ...reply, replies: reply.replies || [] });
            return true;
          }
          if (comment.replies && findAndAddReply(comment.replies)) return true;
        }
        return false;
      };

      if (!findAndAddReply(state.comments)) {
        state.comments.unshift({ ...reply, replies: reply.replies || [] });
      }
    },
    SET_PAGINATION(state, pagination) { state.pagination = pagination; },
    SET_ORDERING(state, ordering) { state.ordering = ordering; },
    SET_CURRENT_PAGE(state, page) { state.currentPage = page; },
  },
  actions: {
    async fetchComments({ commit, state }, { baseUrl, page, ordering } = {}) {
      try {
        const url = (baseUrl || API_BASE).replace(/\/$/, '');
        const currentPage = page || state.currentPage;
        const currentOrdering = ordering || state.ordering;

        const response = await axios.get(`${url}/comments/`, {
          params: { page: currentPage, ordering: currentOrdering },
          withCredentials: true,
        });

        commit('SET_COMMENTS', response.data.results);
        commit('SET_PAGINATION', {
          next: response.data.next,
          previous: response.data.previous,
          count: response.data.count,
        });
        commit('SET_CURRENT_PAGE', currentPage);
      } catch (err) {
        console.error('Failed to fetch comments:', err);
      }
    },
    addComment({ commit }, comment) {
      commit('ADD_COMMENT', comment);
    },
  },
});
