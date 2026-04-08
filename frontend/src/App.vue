<template>
  <router-view />
</template>

<script setup>
// 使用 Vue Router 来管理页面
</script>

<style>
:root {
  /* Nexus Design Tokens - Dark Mode Core */
  --nexus-bg: #0a0b10;
  --nexus-primary: #6366f1; /* Nexus Indigo */
  --nexus-secondary: #a855f7; /* Nexus Purple */
  --nexus-accent: #8b5cf6;
  --nexus-text: #f8fafc;
  --nexus-subtext: #94a3b8;
  --nexus-border: rgba(255, 255, 255, 0.1);
  --nexus-glass: rgba(20, 21, 31, 0.6);
  --nexus-glass-heavy: rgba(30, 31, 46, 0.85);
  --nexus-blur: blur(12px);
  
  /* Legacy mapping support - Force themed colors */
  --black: #0a0b10;
  --white: #ffffff;
  --orange: var(--nexus-primary);
  --gray-light: rgba(255, 255, 255, 0.05);
  --gray-text: var(--nexus-subtext);
  --border: var(--nexus-border);
  
  /* Typography */
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Space Grotesk', system-ui, sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background-color: var(--nexus-bg);
  color: var(--nexus-text);
}

#app {
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Global Glassmorphism Utility */
.glass-panel {
  background: var(--nexus-glass);
  backdrop-filter: var(--nexus-blur);
  border: 1px solid var(--nexus-border);
  border-radius: 12px;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--nexus-glass-heavy);
  border-radius: 10px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--nexus-primary);
}

button {
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
