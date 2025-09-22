import { createStore } from 'vuex';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/';

export default createStore({
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
        replies: comment.replies || []
      }));
    },
    ADD_COMMENT(state, comment) {
      state.comments.unshift({ ...comment, replies: comment.replies || [] });
    },
    ADD_REPLY(state, { parentId, reply }) {
      // Рекурсивно шукаємо батьківський коментар у каскаді
      const findAndAddReply = (comments) => {
        for (let comment of comments) {
          if (comment.id === parentId) {
            comment.replies = comment.replies || [];
            comment.replies.push({ ...reply, replies: reply.replies || [] });
            return true;
          }
          if (comment.replies && findAndAddReply(comment.replies)) {
            return true;
          }
        }
        return false;
      };

      if (!findAndAddReply(state.comments)) {
        // Якщо не знайдено, додаємо як кореневий (резерв)
        state.comments.unshift({ ...reply, replies: reply.replies || [] });
      }
    },
    SET_PAGINATION(state, pagination) {
      state.pagination = pagination;
    },
    SET_ORDERING(state, ordering) {
      state.ordering = ordering;
    },
  },
  actions: {
    async fetchComments({ commit, state }, page = 1) {
      try {
        const response = await axios.get(`${API_BASE}comments/`, {
          params: { page, ordering: state.ordering },
        });
        commit('SET_COMMENTS', response.data.results);
        commit('SET_PAGINATION', {
          next: response.data.next,
          previous: response.data.previous,
          count: response.data.count,
        });
      } catch (error) {
        console.error('Error fetching comments:', error);
      }
    },
    addComment({ commit }, comment) {
      commit('ADD_COMMENT', comment);
    },
  },
});