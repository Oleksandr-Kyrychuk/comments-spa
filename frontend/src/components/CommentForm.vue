<template>
  <div class="form-container">
    <form @submit.prevent="submitForm">
      <!-- Username -->
      <div class="form-group">
        <label>Username</label>
        <input
          v-model="form.user_name"
          placeholder="Letters and digits only"
          required
          pattern="^[a-zA-Z0-9]+$"
          class="form-control"
        />
      </div>

      <!-- Email -->
      <div class="form-group">
        <label>Email</label>
        <input
          v-model="form.email"
          type="email"
          placeholder="Enter valid email"
          required
          class="form-control"
        />
      </div>

      <!-- Home Page -->
      <div class="form-group">
        <label>Home Page (optional)</label>
        <input
          v-model="form.home_page"
          type="url"
          placeholder="https://example.com"
          class="form-control"
        />
      </div>

      <!-- Comment -->
      <div class="form-group">
        <label>Comment</label>
        <div class="tag-panel">
          <button type="button" @click="insertTag('i')" class="btn btn-secondary">[i]</button>
          <button type="button" @click="insertTag('strong')" class="btn btn-secondary">[strong]</button>
          <button type="button" @click="insertTag('code')" class="btn btn-secondary">[code]</button>
          <button type="button" @click="insertTag('a')" class="btn btn-secondary">[a]</button>
        </div>
        <textarea
          v-model="form.text"
          placeholder="Text (supports <a>, <code>, <i>, <strong>)"
          required
          maxlength="5000"
          class="form-control"
        ></textarea>
      </div>

      <!-- Parent Comment -->
      <div class="form-group" v-if="!localParentId">
        <label>Parent Comment (optional)</label>
        <select v-model="form.parent" class="form-control">
          <option value="">No parent</option>
          <option v-for="comment in parentComments" :key="comment.id" :value="comment.id">
            {{ comment.user_name }} ({{ formatDate(comment.created_at) }})
          </option>
        </select>
      </div>

      <!-- File Upload -->
      <div class="form-group">
        <label>Upload File (JPG/GIF/PNG or TXT)</label>
        <input type="file" @change="handleFile" class="form-control" />
      </div>

      <!-- CAPTCHA -->
      <div class="form-group">
        <label>CAPTCHA</label>
        <img :src="captchaImage" alt="CAPTCHA" class="captcha-image" />
        <button type="button" @click="refreshCaptcha" class="btn btn-secondary">Refresh CAPTCHA</button>
        <input
          v-model="form.captcha_1"
          placeholder="Enter CAPTCHA code"
          required
          class="form-control"
        />
        <input v-model="form.captcha_0" type="hidden" />
      </div>

      <!-- Preview -->
      <div class="form-group">
        <button type="button" @click="previewText" class="btn btn-info">Preview</button>
        <div v-if="preview" class="preview-box" v-html="preview"></div>
      </div>

      <!-- Submit -->
      <div class="form-group">
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary">Submit</button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios';
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useStore } from 'vuex';

// Визначаємо базові URL-адреси для роботи через Nginx або локально
const API_BASE = process.env.VUE_APP_API_BASE || '/api';
const WS_BASE = process.env.VUE_APP_WS_BASE || 'ws://localhost:8080/ws/comments/';
const CAPTCHA_URL = process.env.VUE_APP_CAPTCHA_URL || '/captcha/refresh/';
const CSRF_URL = process.env.VUE_APP_CSRF_URL || '/csrf-cookie/';

export default {
  props: {
    parentId: { type: [String, Number], default: null },
  },
  emits: ['submitted'],
  setup(props, { emit }) {
    const store = useStore();
    const localParentId = ref(props.parentId);
    const form = ref({
      user_name: '',
      email: '',
      home_page: '',
      text: '',
      parent: props.parentId || null,
      file: null,
      captcha_0: '',
      captcha_1: '',
    });
    const captchaImage = ref('');
    const preview = ref('');
    const error = ref('');
    const parentComments = ref([]);
    let socket = null;

    // Sync parentId with local state
    watch(() => props.parentId, (newVal) => {
      localParentId.value = newVal;
      form.value.parent = newVal || null;
    });

    const getCsrfToken = async () => {
      try {
        await axios.get(CSRF_URL, { withCredentials: true });
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken'))?.split('=')[1];
        return cookie || null;
      } catch (err) {
        error.value = 'Failed to retrieve CSRF token';
        console.error('CSRF Token Error:', err);
        return null;
      }
    };

    const refreshCaptcha = async () => {
      try {
        const timestamp = Date.now();
        const { data } = await axios.get(`${CAPTCHA_URL}?_=${timestamp}`, {
          withCredentials: true,
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        form.value.captcha_0 = data.key;
        captchaImage.value = `${API_BASE}/../captcha/image/${data.key}/?_=${timestamp}`;
      } catch (err) {
        error.value = 'Failed to refresh CAPTCHA';
        console.error('Captcha Error:', err);
      }
    };

    const connectWebSocket = () => {
      socket = new WebSocket(WS_BASE);
      socket.onopen = () => console.log('WebSocket connected');
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_comment') {
          if (data.comment.parent) {
            store.commit('ADD_REPLY', { parentId: data.comment.parent, reply: data.comment });
          } else {
            store.commit('ADD_COMMENT', data.comment);
          }
        }
      };
      socket.onclose = () => console.log('WebSocket disconnected');
      socket.onerror = (err) => console.error('WebSocket error:', err);
    };

    const previewText = async () => {
      try {
        const { data } = await axios.post(`${API_BASE}/preview/`, { text: form.value.text }, {
          withCredentials: true,
        });
        preview.value = data.preview;
      } catch (err) {
        error.value = 'Failed to fetch preview';
        console.error('Preview Error:', err);
      }
    };

    const handleFile = (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const validTypes = ['image/jpeg', 'image/gif', 'image/png', 'text/plain'];
      if (!validTypes.includes(file.type)) {
        error.value = 'Invalid file type. Use JPG, GIF, PNG, or TXT.';
        return;
      }

      if (file.type === 'text/plain' && file.size > 100 * 1024) {
        error.value = 'TXT file must be <= 100KB';
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        error.value = 'File size must be <= 5MB';
        return;
      }

      form.value.file = file;
    };



    const submitForm = async () => {
  error.value = '';
  if (!form.value.captcha_1) {
    error.value = 'Please enter CAPTCHA';
    return;
  }

  const csrftoken = await getCsrfToken();
  if (!csrftoken) return;

  const payload = {
    user: {
      username: form.value.user_name,
      email: form.value.email,
      homepage: form.value.home_page || '',
    },
    text: form.value.text,
    parent: form.value.parent || null,
    captcha_0: form.value.captcha_0,
    captcha_1: form.value.captcha_1,
  };

  // If a file is present, use FormData for file upload
  if (form.value.file instanceof File) {
    const formData = new FormData();
    formData.append('user', JSON.stringify(payload.user));
    formData.append('text', payload.text);
    if (payload.parent) formData.append('parent', payload.parent);
    formData.append('file', form.value.file);
    formData.append('captcha_0', payload.captcha_0);
    formData.append('captcha_1', payload.captcha_1);

    try {
      const response = await axios.post(`${API_BASE}/comments/`, formData, {
        headers: {
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest',
        },
        withCredentials: true,
      });

      // Форматуємо коментар для відповідності структурі CommentItem
      const newComment = {
        id: null, // ID прийде через WebSocket
        user: response.data.data.user, // Використовуємо user із response.data.data
        text: response.data.data.text,
        parent: response.data.data.parent,
        file: form.value.file ? URL.createObjectURL(form.value.file) : null,
        created_at: new Date().toISOString(),
        replies: [],
      };

      // Очищення форми
      Object.assign(form.value, {
        user_name: '',
        email: '',
        home_page: '',
        text: '',
        parent: localParentId.value || null,
        file: null,
        captcha_0: '',
        captcha_1: '',
      });
      preview.value = '';
      await refreshCaptcha();

      emit('submitted', { ...form.value, parentId: localParentId.value, comment: newComment });
    } catch (err) {
      error.value = JSON.stringify(err.response?.data) || 'Failed to submit comment';
      console.error('Submit Error:', err);
    }
  } else {
    // Send as JSON if no file
    try {
      const response = await axios.post(`${API_BASE}/comments/`, payload, {
        headers: {
          'X-CSRFToken': csrftoken,
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/json',
        },
        withCredentials: true,
      });

      // Форматуємо коментар для відповідності структурі CommentItem
      const newComment = {
        id: null, // ID прийде через WebSocket
        user: response.data.data.user, // Використовуємо user із response.data.data
        text: response.data.data.text,
        parent: response.data.data.parent,
        file: null,
        created_at: new Date().toISOString(),
        replies: [],
      };

      // Очищення форми
      Object.assign(form.value, {
        user_name: '',
        email: '',
        home_page: '',
        text: '',
        parent: localParentId.value || null,
        file: null,
        captcha_0: '',
        captcha_1: '',
      });
      preview.value = '';
      await refreshCaptcha();

      emit('submitted', { ...form.value, parentId: localParentId.value, comment: newComment });
    } catch (err) {
      error.value = JSON.stringify(err.response?.data) || 'Failed to submit comment';
      console.error('Submit Error:', err);
    }
  }
};



    const insertTag = (tag) => {
      const cursorPos = form.value.text.length;
      form.value.text += `<${tag}>Your text here</${tag}>`;
      setTimeout(() => {
        const textarea = document.querySelector('textarea');
        if (textarea) {
          textarea.focus();
          textarea.setSelectionRange(cursorPos + 2, cursorPos + 12);
        }
      }, 0);
    };

    const fetchParentComments = async () => {
  if (!localParentId.value) {
    try {
      const { data } = await axios.get(`${API_BASE}/comments/?ordering=-created_at`, {
        withCredentials: true,
      });
      parentComments.value = data.results.filter(c => !c.parent);
    } catch (err) {
      console.error('Error fetching parent comments:', err);
    }
  }
};

    const formatDate = (date) => new Date(date).toLocaleString();

    onMounted(() => {
      refreshCaptcha();
      connectWebSocket();
      fetchParentComments();
    });

    onUnmounted(() => {
      if (socket) socket.close();
    });

    return {
      form,
      captchaImage,
      preview,
      error,
      refreshCaptcha,
      previewText,
      handleFile,
      submitForm,
      insertTag,
      parentComments,
      formatDate,
      localParentId,
    };
  },
};
</script>

<style scoped>
.form-container { padding: 20px; }
.form-group { margin-bottom: 15px; }
.form-control { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
.tag-panel { margin-bottom: 5px; }
.btn { padding: 5px 10px; margin-right: 5px; }
.error { color: red; }
.preview-box { border: 1px solid #ddd; padding: 10px; margin-top: 10px; }
.captcha-image { max-width: 200px; margin-bottom: 10px; }
</style>