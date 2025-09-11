<template>
  <tr>
    <td>{{ comment.user_name }}</td>
    <td>{{ comment.email }}</td>
    <td v-html="comment.text"></td>
    <td>
      <template v-if="comment.file">
        <a v-if="isTextFile" :href="mediaUrl + comment.file" download>Download TXT</a>
        <img
          v-else
          :src="mediaUrl + comment.file"
          @click="openLightbox(mediaUrl + comment.file)"
          style="max-width:320px;"
        />
      </template>
      <EasyLightbox
        :visible="visible"
        :imgs="[lightboxUrl]"
        @hide="visible = false"
      />
    </td>
    <td>{{ comment.created_at }}</td>
  </tr>
  <tr v-if="comment.replies && comment.replies.length">
    <td colspan="5">
      <table style="margin-left:20px;">
        <CommentItem v-for="reply in comment.replies" :key="reply.id" :comment="reply" />
      </table>
    </td>
  </tr>
</template>

<script>
import { ref } from 'vue';
import EasyLightbox from 'vue-easy-lightbox';

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
    const isTextFile = props.comment.file?.endsWith('.txt');
    return { mediaUrl, isTextFile, openLightbox, visible, lightboxUrl };
  },
};
</script>
