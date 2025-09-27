<!-- CommentItem.vue -->
<template>
  <div class="comment-block" :style="{ marginLeft: level * 20 + 'px' }">
    <img :src="avatarUrl" class="avatar" alt="Avatar" />
    <div class="content">
      <!-- Reply to parent -->
      <div v-if="comment.parent_username" class="reply-to">
        Reply to: <span class="username">{{ comment.parent_username }}</span>
      </div>

      <!-- Header -->
      <div class="header">
        <span class="username">{{ comment.user?.username || 'Анонім' }}</span>
        <span class="time">{{ formatDate(comment.created_at) }}</span>
      </div>

      <!-- Comment text -->
      <div class="text" v-html="comment.text"></div>

      <!-- Email & Home Page -->
      <div v-if="comment.user?.email">
        Email: <a :href="'mailto:' + comment.user.email">{{ comment.user.email }}</a>
      </div>
      <div v-if="comment.user?.homepage">
        Home: <a :href="comment.user.homepage" target="_blank">{{ comment.user.homepage }}</a>
      </div>

      <!-- File upload -->
      <div v-if="comment.file">
        <template v-if="isTextFile">
          <a :href="getFileUrl(comment.file)" download>Download TXT</a>
        </template>
        <img
          v-else
          :src="getFileUrl(comment.file)"
          @click="openLightbox(getFileUrl(comment.file))"
          style="max-width: 320px; cursor: pointer"
        />
      </div>

      <!-- Reply button -->
      <button v-if="comment.id" @click="showReplyForm = !showReplyForm" class="btn btn-link">Reply</button>

      <!-- Reply form -->
      <div v-if="showReplyForm" class="reply-form">
        <CommentForm :parentId="comment.id" @submitted="addReply" />
      </div>

      <!-- Lightbox -->
      <EasyLightbox v-model:visible="visible" :imgs="[lightboxUrl]" />

      <!-- Replies -->
      <div v-if="comment.replies?.length" class="replies">
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
    const getFileUrl = (filePath) =>
      filePath ? (filePath.startsWith(mediaUrl) ? filePath : mediaUrl + filePath) : '';

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
.comment-block {
  display: flex;
  margin: 10px 0;
  padding: 10px;
  border-bottom: 1px solid #ddd;
  border-left: 3px solid #ccc;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  margin-right: 10px;
}
.content {
  flex: 1;
}
.header {
  font-weight: bold;
  color: #333;
  margin-bottom: 5px;
}
.time {
  font-size: 0.8em;
  color: #888;
  margin-left: 10px;
}
.text {
  margin: 5px 0;
}
.replies {
  padding-left: 15px;
  border-left: 3px solid #ccc;
}
.reply-form {
  margin-top: 10px;
}
.reply-to {
  font-size: 0.9em;
  color: #555;
  margin-bottom: 5px;
  font-style: italic;
}
.username {
  color: #007bff;
}
</style>