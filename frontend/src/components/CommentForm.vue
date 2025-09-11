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
        <button type="button" @click="refreshCaptcha" class="btn btn-secondary">Refresh CAPTCHA</button>
        <input
          v-model="form.captcha_code"
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
      captcha_hashkey: '',
      captcha_code: '',
    });
    const captchaImage = ref('');
    const preview = ref('');
    const error = ref('');

    const getCsrfToken = async () => {
      try {
        await axios.get(`${API_BASE}/csrf-cookie/`, { withCredentials: true });
        const csrftoken = document.cookie
          .split('; ')
          .find(row => row.startsWith('csrftoken='))
          ?.split('=')[1] || '';
        return csrftoken;
      } catch (err) {
        console.error('Failed to fetch CSRF token:', err);
        throw err;
      }
    };

    const refreshCaptcha = async () => {
      try {
        error.value = '';
        const csrftoken = await getCsrfToken();
        const response = await axios.post(
          `${API_BASE}/captcha/refresh/`,
          {},
          { headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' }, withCredentials: true }
        );
        form.value.captcha_hashkey = response.data.key;
        captchaImage.value = `${API_BASE}${response.data.image_url.startsWith('/') ? '' : '/'}${response.data.image_url}`;
      } catch (err) {
        error.value = 'Не вдалося завантажити CAPTCHA';
        console.error(err);
      }
    };

    const previewText = async () => {
      try {
        error.value = '';
        const csrftoken = await getCsrfToken();
        const response = await axios.post(
          `${API_BASE}/api/preview/`,
          { text: form.value.text },
          { headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' }, withCredentials: true }
        );
        preview.value = response.data.preview;
      } catch (err) {
        error.value = 'Не вдалося завантажити попередній перегляд';
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
          if (key === 'file' && form.value[key] instanceof File) formData.append(key, form.value[key]);
          else if (form.value[key] !== '' && key !== 'file') formData.append(key, form.value[key]);
        });

        const response = await axios.post(`${API_BASE}/api/comments/`, formData, {
          headers: { 'X-CSRFToken': csrftoken, 'X-Requested-With': 'XMLHttpRequest' },
          withCredentials: true,
        });

        console.log('Submit response:', response.data);
        store.dispatch('addComment', form.value);

        form.value = { user_name:'', email:'', home_page:'', text:'', parent:'', file:null, captcha_hashkey:'', captcha_code:'' };
        preview.value = '';
        await refreshCaptcha();
      } catch (err) {
        error.value = err.response?.data?.file?.[0] || err.response?.data?.detail || 'Не вдалося відправити коментар';
        console.error(err);
      }
    };

    const init = async () => {
      try { await getCsrfToken(); await refreshCaptcha(); }
      catch (err) { console.error(err); error.value = 'Не вдалося ініціалізувати CSRF або CAPTCHA'; }
    };

    init();

    return { form, captchaImage, preview, error, refreshCaptcha, previewText, handleFile, submitForm };
  },
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
</style>
