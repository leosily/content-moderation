<template>
  <main class="app-shell">
    <router-view />
  </main>
</template>

<script setup>
// 入口组件只负责承载路由视图
</script>

<style>
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: radial-gradient(circle at 10% 10%, #eef3ff 0%, #f6f8fc 42%, #f4f7ff 100%);
  color: #1f2937;
}

a {
  color: inherit;
}

.app-shell {
  min-height: 100vh;
}
</style>

