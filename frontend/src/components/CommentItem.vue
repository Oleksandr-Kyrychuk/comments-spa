<!-- CommentItem.vue -->
<template>
  <div class="flex mb-4 p-4 border-b border-l-4 border-gray-300" :style="{ marginLeft: level * 20 + 'px' }">
    <img :src="avatarUrl" class="w-10 h-10 rounded-full mr-3" alt="Avatar" />
    <div class="flex-1">
      <!-- Reply to parent -->
      <div v-if="comment.parent_username" class="text-sm text-gray-600 italic mb-2">
        Відповідь для: <span class="text-blue-500">{{ comment.parent_username }}</span>
      </div>

      <!-- Header -->
      <div class="flex items-center mb-2">
        <span class="font-bold text-blue-500">{{ comment.user?.username || 'Анонім' }}</span>
        <span class="text-sm text-gray-500 ml-2">{{ formatDate(comment.created_at) }}</span>
      </div>

      <!-- Comment text -->
      <div class="text-gray-800 mb-2" v-html="comment.text"></div>

      <!-- Email & Home Page -->
      <div v-if="comment.user?.email" class="text-sm">
        Email: <a :href="'mailto:' + comment.user.email" class="text-blue-500">{{ comment.user.email }}</a>
      </div>
      <div v-if="comment.user?.homepage" class="text-sm">
        Домашня сторінка: <a :href="comment.user.homepage" target="_blank" class="text-blue-500">{{ comment.user.homepage }}</a>
      </div>

      <!-- File upload -->
      <div v-if="comment.file" class="mt-2">
        <template v-if="isTextFile">
          <a :href="getFileUrl(comment.file)" download class="text-blue-500">Завантажити TXT</a>
        </template>
        <img
          v-else
          :src="getFileUrl(comment.file)"
          @click="openLightbox(getFileUrl(comment.file))"
          class="max-w-xs cursor-pointer"
        />
      </div>

      <!-- Reply button -->
      <button v-if="comment.id" @click="showReplyForm = !showReplyForm" class="text-blue-500 mt-2">Відповісти</button>

      <!-- Reply form -->
      <div v-if="showReplyForm" class="mt-4">
        <CommentForm :parentId="comment.id" @submitted="addReply" />
      </div>

      <!-- Lightbox -->
      <EasyLightbox v-model:visible="visible" :imgs="[lightboxUrl]" />

      <!-- Replies -->
      <div v-if="comment.replies?.length" class="mt-4 pl-4 border-l-4 border-gray-300">
        <CommentItem
          v-for="reply in comment.replies"
          :key="reply.id || reply.tempId"
          :comment="reply"
          :level="level + 1"
          @add-reply="handleAddReply"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import EasyLightbox from 'vue-easy-lightbox';
import CommentForm from './CommentForm.vue';
import md5 from 'md5';

const mediaUrl = process.env.VUE_APP_API_BASE
  ? `${process.env.VUE_APP_API_BASE}/media/`
  : 'http://localhost:8000/media/';

export default {
  name: 'CommentItem',
  props: {
    comment: { type: Object, required: true },
    level: { type: Number, default: 0 },
  },
  components: { EasyLightbox, CommentForm },
  emits: ['add-reply'],
  setup(props, { emit }) {
    const visible = ref(false);
    const lightboxUrl = ref('');
    const showReplyForm = ref(false);

    const openLightbox = (url) => {
      lightboxUrl.value = url;
      visible.value = true;
    };

    const addReply = (newComment) => {
      showReplyForm.value = false;
      emit('add-reply', { parentId: props.comment.id, reply: newComment.comment });
    };

    const handleAddReply = (payload) => {
      emit('add-reply', payload);
    };

    const isTextFile = computed(() => props.comment.file?.endsWith('.txt') || false);
    const avatarUrl = computed(() =>
      `https://www.gravatar.com/avatar/${md5(props.comment.user?.email || '')}?s=40&d=identicon`
    );
    const formatDate = (dateStr) => new Date(dateStr).toLocaleString();
    const getFileUrl = (filePath) => {
  if (!filePath) return '';
  if (filePath.startsWith('http') || filePath.startsWith('blob')) {
    return filePath;  // Для blob або full http
  }
  // Нормалізуємо: видаляємо /media/ якщо є, щоб додати mediaUrl
  const normalized = filePath.replace(/^\/media\//, '');
  return mediaUrl + normalized;  // mediaUrl вже включає /media/
};

    return {
      isTextFile,
      avatarUrl,
      formatDate,
      openLightbox,
      visible,
      lightboxUrl,
      showReplyForm,
      getFileUrl,
      addReply,
      handleAddReply,
    };
  },
};
</script>

<style scoped>
</style>