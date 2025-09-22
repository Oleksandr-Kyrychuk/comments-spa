<template>
  <div class="comment-block">
    <img :src="avatarUrl" class="avatar" alt="Avatar" />
    <div class="content">
      <!-- Reply to parent -->
      <div v-if="parentUsername" class="reply-to">
        Відповідь на: <span class="username">{{ parentUsername }}</span>
      </div>

      <!-- Header -->
      <div class="header">
        <span class="username">{{ comment.user_name }}</span>
        <span class="time">{{ formatDate(comment.created_at) }}</span>
      </div>

      <!-- Comment text -->
      <div class="text" v-html="comment.text"></div>

      <!-- Email & Home Page -->
      <div v-if="comment.email">Email: <a :href="'mailto:' + comment.email">{{ comment.email }}</a></div>
      <div v-if="comment.home_page">Home: <a :href="comment.home_page" target="_blank">{{ comment.home_page }}</a></div>

      <!-- File upload -->
      <div v-if="comment.file">
        <template v-if="isTextFile">
          <a :href="getFileUrl(comment.file)" download>Download TXT</a>
        </template>
        <img
          v-else
          :src="getFileUrl(comment.file)"
          @click="openLightbox(getFileUrl(comment.file))"
          style="max-width:320px; cursor: pointer;"
        />
      </div>

      <!-- Reply button -->
      <button @click="showReplyForm = !showReplyForm" class="btn btn-link">Reply</button>

      <!-- Reply form -->
      <div v-if="showReplyForm" class="reply-form">
        <CommentForm :parentId="comment.id" @submitted="addReply"/>
      </div>

      <!-- Lightbox -->
      <EasyLightbox v-model:visible="visible" :imgs="[lightboxUrl]" />
    </div>

    <!-- Replies -->
    <div v-if="comment.replies?.length" class="replies">
      <CommentItem
        v-for="reply in comment.replies"
        :key="reply.id"
        :comment="reply"
        @add-reply="handleAddReply"
      />
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import EasyLightbox from 'vue-easy-lightbox';
import CommentForm from './CommentForm.vue';
import md5 from 'md5';
import { useStore } from 'vuex';

const mediaUrl = 'http://localhost:8000/media/';

export default {
  name: 'CommentItem', // обов’язково для рекурсії
  props: {
    comment: { type: Object, required: true }
  },
  components: { EasyLightbox, CommentForm, CommentItem: null }, // CommentItem буде саморекурсивним
  emits: ['add-reply'],
  setup(props, { emit }) {
    const store = useStore();

    const visible = ref(false);
    const lightboxUrl = ref('');
    const showReplyForm = ref(false);

    const openLightbox = (url) => {
      lightboxUrl.value = url;
      visible.value = true;
    };

    const addReply = (newComment) => {
      showReplyForm.value = false;
      emit('add-reply', { parentId: props.comment.id, reply: newComment });
    };

    const handleAddReply = (payload) => {
      emit('add-reply', payload);
    };

    const isTextFile = computed(() => props.comment.file?.endsWith('.txt') || false);
    const avatarUrl = computed(() => `https://www.gravatar.com/avatar/${md5(props.comment.email || '')}?s=40&d=identicon`);
    const formatDate = (dateStr) => new Date(dateStr).toLocaleString();
    const getFileUrl = (filePath) => filePath ? (filePath.startsWith(mediaUrl) ? filePath : mediaUrl + filePath) : '';

    // Батьківський username
    const parentUsername = computed(() => {
      if (!props.comment.parent) return '';
      const findParent = (comments, parentId) => {
        for (let comment of comments) {
          if (String(comment.id) === String(parentId)) return comment.user_name;
          if (comment.replies?.length) {
            const res = findParent(comment.replies, parentId);
            if (res) return res;
          }
        }
        return '';
      };
      return store.state.comments.length ? findParent(store.state.comments, props.comment.parent) : '';
    });

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
      parentUsername
    };
  }
};
</script>

<style scoped>
.comment-block { display: flex; margin: 10px 0; padding: 10px; border-bottom: 1px solid #ddd; }
.avatar { width: 40px; height: 40px; border-radius: 50%; margin-right: 10px; }
.content { flex: 1; }
.header { font-weight: bold; color: #333; margin-bottom: 5px; }
.time { font-size: 0.8em; color: #888; margin-left: 10px; }
.text { margin: 5px 0; }
.replies { margin-left: 50px; border-left: 2px solid #eee; padding-left: 10px; }
.reply-form { margin-top: 10px; }
.reply-to { font-size: 0.9em; color: #555; margin-bottom: 5px; }
.username { color: #007bff; }
</style>
