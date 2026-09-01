const path = require('path')
const { defineConfig } = require('vite')

module.exports = defineConfig({
  build: {
    target: 'es2015',
    lib: {
      entry: path.resolve(__dirname, 'src/main.js'),
      name: 'markdown-renderer',
      fileName: (format) => `markdown-renderer.${format}.js`,
      formats: ['es']
    }
  }
})
