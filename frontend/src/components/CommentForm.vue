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
            {{ comment.user?.username || comment.user_name }} ({{ formatDate(comment.created_at) }})
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
import { ref, onMounted, watch, toRaw } from 'vue';
import { useStore } from 'vuex';
import { v4 as uuidv4 } from 'uuid';

const API_BASE = process.env.VUE_APP_API_BASE || '/api';
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

    // Логування ініціалізації parentId
    console.log('CommentForm initialized with parentId:', props.parentId);

    // Sync parentId with local state
    watch(() => props.parentId, (newVal) => {
      console.log('ParentId changed to:', newVal);
      localParentId.value = newVal;
      form.value.parent = newVal || null;
    });

    const getCsrfToken = async () => {
      try {
        console.log('Fetching CSRF token from:', CSRF_URL);
        await axios.get(CSRF_URL, { withCredentials: true });
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken'))?.split('=')[1];
        console.log('CSRF token retrieved:', cookie);
        return cookie || null;
      } catch (err) {
        error.value = 'Failed to retrieve CSRF token';
        console.error('CSRF Token Error:', err);
        return null;
      }
    };

    const refreshCaptcha = async () => {
      try {
        console.log('Refreshing CAPTCHA from:', CAPTCHA_URL);
        const timestamp = Date.now();
        const { data } = await axios.get(`${CAPTCHA_URL}?_=${timestamp}`, {
  withCredentials: true,
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
});
console.log('CAPTCHA response:', data);
        console.log('CAPTCHA data:', data);
        form.value.captcha_0 = data.key;
        captchaImage.value = `${API_BASE}/../captcha/image/${data.key}/?_=${timestamp}`;
        console.log('CAPTCHA key set:', data.key);
      } catch (err) {
        error.value = 'Failed to refresh CAPTCHA';
        console.error('Captcha Error:', err);
      }
    };

    const previewText = async () => {
      try {
        console.log('Previewing text:', form.value.text);
        const { data } = await axios.post(`${API_BASE}/preview/`, { text: form.value.text }, {
          withCredentials: true,
          headers: { 'X-Requested-With': 'XMLHttpRequest' },
        });
        console.log('Preview response:', data);
        preview.value = data.preview;
      } catch (err) {
        error.value = 'Failed to preview comment';
        console.error('Preview Error:', err);
      }
    };

    const handleFile = (event) => {
      const file = event.target.files[0];
      console.log('File selected:', file?.name, 'Type:', file?.type, 'Size:', file?.size);
      if (!file) return;

      const allowedTypes = ['image/jpeg', 'image/gif', 'image/png', 'text/plain'];
      if (!allowedTypes.includes(file.type)) {
        error.value = 'File type must be JPG, GIF, PNG, or TXT';
        console.error('Invalid file type:', file.type);
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        error.value = 'File size must be <= 5MB';
        console.error('File size too large:', file.size);
        return;
      }

      form.value.file = file;
      console.log('File set to form:', file.name);
    };

    const submitForm = async () => {
      error.value = '';
      console.log('Submitting form with data:', { ...form.value, file: form.value.file?.name });

      if (!form.value.captcha_1) {
        error.value = 'Please enter CAPTCHA';
        console.error('CAPTCHA input missing');
        return;
      }

      // Перевірка parentId
      if (form.value.parent) {
        // Рекурсивний пошук коментаря за id
        const findComment = (comments, id) => {
          const rawComments = toRaw(comments);
          for (const c of rawComments) {
            if (c.id === Number(id)) return c;
            if (c.replies?.length) {
              const found = findComment(c.replies, id);
              if (found) return found;
            }
          }
          return null;
        };

        const parentExists = findComment(store.state.comments?.comments || [], form.value.parent);
        console.log('Checking parentId:', form.value.parent, 'Exists:', !!parentExists);
        if (!parentExists) {
          error.value = 'Selected parent comment does not exist';
          console.error('Parent comment not found in store:', form.value.parent);
          return;
        }
      }

      const csrftoken = await getCsrfToken();
      if (!csrftoken) {
        console.error('No CSRF token, aborting submission');
        return;
      }

      const tempId = uuidv4();
      console.log('Generated tempId:', tempId);

      const payload = new FormData();
      payload.append('user_name', form.value.user_name);
      payload.append('email', form.value.email);
      payload.append('home_page', form.value.home_page || '');
      payload.append('text', form.value.text);
      if (form.value.parent) {
        const parentId = Number(form.value.parent);
        payload.append('parent', parentId);
        console.log('Appending parentId:', parentId);
      }
      if (form.value.file) {
        payload.append('file', form.value.file);
        console.log('Appending file:', form.value.file.name);
      }
      payload.append('captcha_0', form.value.captcha_0);
      payload.append('captcha_1', form.value.captcha_1);
      payload.append('tempId', tempId);

      // Логування payload
      console.log('Payload entries:', [...payload.entries()]);

      // Створюємо локальний об'єкт коментаря для миттєвого відображення
      const findParentComment = (comments, id) => {
        const rawComments = toRaw(comments);
        for (const c of rawComments) {
          if (c.id === Number(id)) return c;
          if (c.replies?.length) {
            const found = findParentComment(c.replies, id);
            if (found) return found;
          }
        }
        return null;
      };

      const newComment = {
        id: null,
        tempId,
        user: {
          username: form.value.user_name,
          email: form.value.email,
          homepage: form.value.home_page || '',
        },
        text: form.value.text,
        parent: form.value.parent ? Number(form.value.parent) : null,
        parent_username: form.value.parent
          ? findParentComment(store.state.comments?.comments || [], form.value.parent)?.user?.username
          : null,
        file: form.value.file ? URL.createObjectURL(form.value.file) : null,
        created_at: new Date().toISOString(),
        replies: [],
      };
      console.log('Created local comment object:', newComment);

      try {
        console.log('Sending POST request to:', `${API_BASE}/comments/`);
        const response = await axios.post(`${API_BASE}/comments/`, payload, {
          headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
          },
          withCredentials: true,
        });

        console.log('Server response:', response.data);

        // Оновлюємо коментар з серверним ID
        newComment.id = response.data.data?.id || null;
        console.log('Updated comment with server ID:', newComment.id);

        // Очищаємо форму
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
        console.log('Form cleared, refreshing CAPTCHA');
        await refreshCaptcha();

        // Викликаємо подію submitted для оновлення стану
        console.log('Emitting submitted event with:', { ...form.value, parentId: localParentId.value, comment: newComment });
        emit('submitted', { ...form.value, parentId: localParentId.value, comment: newComment });
      } catch (err) {
        error.value = err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Failed to submit comment';
        console.error('Submit Error:', err);
        console.error('Response Data:', err.response?.data);
        console.error('Response Status:', err.response?.status);
      }
    };

    const insertTag = (tag) => {
      console.log('Inserting tag:', tag);
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
          console.log('Fetching parent comments from:', `${API_BASE}/comments/?ordering=-created_at`);
          const { data } = await axios.get(`${API_BASE}/comments/?ordering=-created_at`, {
            withCredentials: true,
          });
          parentComments.value = data.results.filter(c => !c.parent);
          console.log('Parent comments fetched:', parentComments.value);
        } catch (err) {
          console.error('Error fetching parent comments:', err);
        }
      }
    };

    const formatDate = (date) => new Date(date).toLocaleString();

    onMounted(() => {
      console.log('CommentForm mounted');
      refreshCaptcha();
      fetchParentComments();
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