// SvelteKit config — adapter-static for single-page dashboard app
// Static build output goes to build/ directory, served by any static file server
import adapter from '@sveltejs/adapter-static';
export default {
  kit: {
    adapter: adapter({ fallback: 'index.html' })
  }
};
