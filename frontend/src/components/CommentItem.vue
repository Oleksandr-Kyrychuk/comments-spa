<!-- CommentItem.vue -->
<template>
  <div class="comment-block">
    <img :src="avatarUrl" class="avatar" alt="Avatar" />
    <div class="content">
      <div class="header">
        <span class="username">{{ comment.user_name }}</span>
        <span class="time">{{ formatDate(comment.created_at) }}</span>
      </div>
      <div class="text" v-html="comment.text"></div>
      <div v-if="comment.email">Email: <a :href="'mailto:' + comment.email">{{ comment.email }}</a></div>
      <div v-if="comment.home_page">Home: <a :href="comment.home_page" target="_blank">{{ comment.home_page }}</a></div>
      <div v-if="comment.file">
        <template v-if="isTextFile">
          <a :href="mediaUrl + comment.file" download>Download TXT</a>
        </template>
        <img
          v-else
          :src="mediaUrl + comment.file"
          @click="openLightbox(mediaUrl + comment.file)"
          style="max-width:320px; cursor: pointer;"
        />
      </div>
      <EasyLightbox
        :visible="visible"
        :imgs="[lightboxUrl]"
        @hide="visible = false"
      />
    </div>
  </div>
  <div v-if="comment.replies && comment.replies.length" class="replies">
    <CommentItem v-for="reply in comment.replies" :key="reply.id" :comment="reply" />
  </div>
</template>

<script>
import { ref, computed } from 'vue';
import EasyLightbox from 'vue-easy-lightbox';
import md5 from 'md5'; // npm install md5

const mediaUrl = 'http://localhost:8000/media/';

export default {
  props: ['comment'],
  components: { EasyLightbox, CommentItem: () => import('./CommentItem.vue') },
  setup(props) {
    const visible = ref(false);
    const lightboxUrl = ref('');
    const openLightbox = (url) => {
      lightboxUrl.value = url;
      visible.value = true;
    };
    const isTextFile = computed(() => props.comment.file?.endswith('.txt'));
    const avatarUrl = computed(() => `https://www.gravatar.com/avatar/${md5(props.comment.email || '')}?s=40&d=identicon`);
    const formatDate = (dateStr) => new Date(dateStr).toLocaleString();

    return { mediaUrl, isTextFile, openLightbox, visible, lightboxUrl, avatarUrl, formatDate };
  },
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
</style>