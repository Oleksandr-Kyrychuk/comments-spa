import Vuex from 'vuex';
import comments from './modules/comments';// Імпортуємо модуль comments.js

export default Vuex.createStore({
  modules: {
    comments, // Підключаємо модуль comments з неймспейсом
  },
});