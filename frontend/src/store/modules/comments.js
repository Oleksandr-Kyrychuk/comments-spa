import axios from 'axios';

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
    },
    SET_PAGINATION(state, pagination) {
      state.pagination = pagination;
    },
    SET_ORDERING(state, ordering) {
      state.ordering = ordering;
    },
    SET_CURRENT_PAGE(state, page) {
      state.currentPage = page;
    },
    ADD_COMMENT(state, comment) {
      state.comments.unshift(comment);
    },
    ADD_REPLY(state, { parentId, reply }) {
      const parent = state.comments.find(c => c.id === parentId);
      if (parent) parent.replies.push(reply);
    },
  },
  actions: {
    async fetchComments({ commit, state }, { baseUrl, page = 1 }) {
      try {
        const res = await axios.get(`${baseUrl}/comments/`, {
          params: { ordering: state.ordering, page },
        });
        commit('SET_COMMENTS', res.data.results);
        commit('SET_PAGINATION', { previous: res.data.previous, next: res.data.next });
        commit('SET_CURRENT_PAGE', page);
      } catch (err) {
        console.error('Failed to fetch comments:', err);
      }
    },
  },
};

