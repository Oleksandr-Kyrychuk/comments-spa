<!-- CommentForm.vue -->
<template>
  <div class="form-container">
    <form @submit.prevent="submitForm">
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

      <div class="form-group">
        <label>Home Page (optional)</label>
        <input
          v-model="form.home_page"
          type="url"
          placeholder="https://example.com"
          class="form-control"
        />
      </div>

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

      <div class="form-group">
        <label>Parent Comment (optional)</label>
        <select v-model="form.parent" class="form-control">
          <option value="">No parent</option>
        </select>
      </div>

      <div class="form-group">
        <label>Upload File (JPG/GIF/PNG or TXT)</label>
        <input type="file" @change="handleFile" class="form-control" />
      </div>

      <div class="form-group">
        <label>CAPTCHA</label>
        <img :src="captchaImage" alt="CAPTCHA" class="captcha-image" />
        <button type="button" @click="refreshCaptcha" class="btn btn-secondary">
          Refresh CAPTCHA
        </button>
        <input
          v-model="form.captcha_1"
          placeholder="Enter CAPTCHA code"
          required
          class="form-control"
        />
      </div>

      <div class="form-group">
        <button type="button" @click="previewText" class="btn btn-info">Preview</button>
        <div v-if="preview" class="preview-box" v-html="preview"></div>
      </div>

      <div class="form-group">
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" class="btn btn-primary">Submit</button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios';
import { ref } from 'vue';
import { useStore } from 'vuex';

const API_BASE = 'http://localhost:8000';
axios.defaults.withCredentials = true;

export default {
  setup() {
    const store = useStore();
    const form = ref({
      user_name: '',
      email: '',
      home_page: '',
      text: '',
      parent: '',
      file: null,
      captcha_0: '',
      captcha_1: ''
    });
    const captchaImage = ref('');
    const preview = ref('');
    const error = ref('');

    const getCsrfToken = async () => {
      await axios.get(`${API_BASE}/csrf-cookie/`);
      return axios.defaults.headers.common['X-CSRFToken'];
    };

    const refreshCaptcha = async () => {
  try {
    const timestamp = Date.now(); // Для уникнення кешу
    const response = await axios.get(`${API_BASE}/captcha/refresh/?_=${timestamp}`, {
      withCredentials: true,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'  // Обов'язково для проходження перевірки is_ajax()
      }
    });
    form.value.captcha_0 = response.data.key;
    captchaImage.value = `${API_BASE}/captcha/image/${response.data.key}/?_=${timestamp}`;
  } catch (err) {
    console.error(err);
    error.value = 'Не вдалося оновити CAPTCHA';
  }
};


    const previewText = async () => {
      try {
        const response = await axios.post(`${API_BASE}/api/preview/`, { text: form.value.text });
        preview.value = response.data.preview;
      } catch (err) {
        console.error(err);
      }
    };

    const handleFile = (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const validTypes = ['image/jpeg', 'image/gif', 'image/png', 'text/plain'];
      if (!validTypes.includes(file.type)) {
        error.value = 'Неправильний тип файлу. Використовуйте JPG, GIF, PNG або TXT.';
        return;
      }

      if (file.size > 100 * 1024 && file.type === 'text/plain') {
        error.value = 'TXT file must be <= 100KB';
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        error.value = 'Розмір файлу має бути ≤ 5MB';
        return;
      }

      form.value.file = file;
    };

    const submitForm = async () => {
      try {
        error.value = '';
        const csrftoken = await getCsrfToken();
        const formData = new FormData();
        Object.keys(form.value).forEach(key => {
          const value = form.value[key];
          if (key === 'file' && value instanceof File) {
            formData.append(key, value);
          } else {
            formData.append(key, value || '');
          }
        });

        const response = await axios.post(`${API_BASE}/api/comments/`, formData, {
          headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' },
          withCredentials: true,
        });

        store.dispatch('addComment', response.data);
        form.value = { user_name: '', email: '', home_page: '', text: '', parent: '', file: null, captcha_0: '', captcha_1: '' };
        preview.value = '';
        await refreshCaptcha();
      } catch (err) {
        error.value = JSON.stringify(err.response?.data, null, 2) || 'Не вдалося відправити коментар';
        console.error('Full server error:', err.response?.data);
      }
    };

    const insertTag = (tag) => {
      const cursorPos = form.value.text.length;
      form.value.text += `<${tag}>Your text here</${tag}>`;
      setTimeout(() => {
        const textarea = document.querySelector('textarea');
        textarea.focus();
        textarea.setSelectionRange(cursorPos + 2, cursorPos + 12);
      }, 0);
    };

    const init = async () => {
      try {
        await getCsrfToken();
        await refreshCaptcha();
      } catch (err) {
        console.error(err);
        error.value = 'Не вдалося ініціалізувати CSRF або CAPTCHA';
      }
    };

    init();

    return { form, captchaImage, preview, error, refreshCaptcha, previewText, handleFile, submitForm, insertTag };
  }
};
</script>

<style scoped>
.form-container {
  max-width: 600px;
  margin: 20px auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

.form-group { margin-bottom: 15px; }
.form-control { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; }
.captcha-image { display: block; margin: 10px 0; width: 350px; height: auto; image-rendering: crisp-edges; border: 1px solid #ddd; }
.preview-box { margin-top: 10px; padding: 10px; border: 1px solid #ddd; background: #f9f9f9; }
.error { color: red; margin-bottom: 10px; }
.btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
.btn-primary { background: #007bff; color: white; }
.btn-secondary { background: #6c757d; color: white; }
.btn-info { background: #17a2b8; color: white; }
.tag-panel { margin-bottom: 10px; }
.tag-panel .btn { margin-right: 5px; font-size: 0.9em; padding: 4px 8px; }
</style>