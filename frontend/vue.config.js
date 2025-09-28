const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  devServer: { port: 8080 },
  transpileDependencies: true,
  pluginOptions: {
    define: {
      'process.env': {
        VUE_APP_API_BASE: process.env.VUE_APP_API_BASE,
      }
    }
  }
})
