import { createStore } from 'vuex';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/';  // Ваш Django сервер

export default createStore({
  state: {
    comments: [],  // Список кореневих коментарів з replies
    pagination: { next: null, previous: null, count: 0 },
    currentPage: 1,
    ordering: '-created_at',  // Default LIFO
  },
  mutations: {
    SET_COMMENTS(state, comments) {
      state.comments = comments;
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
    async addComment({ dispatch }, commentData) {
      try {
        const formData = new FormData();
        Object.keys(commentData).forEach(key => formData.append(key, commentData[key]));
        await axios.post(`${API_BASE}comments/`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        dispatch('fetchComments');  // Оновити список
      } catch (error) {
        console.error('Error adding comment:', error);
      }
    },
    // Підготовка до WebSocket: пізніше додайте action для real-time update, напр. via WebSocket onmessage -> commit
    // Для junior+: поки polling, напр. setInterval(() => dispatch('fetchComments'), 5000);
  },
});