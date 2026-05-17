# =============================================================================
# Dockerfile — 前端 SPA（Nginx）
# =============================================================================
FROM nginx:alpine

# 复制 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物（dist/ 需先在前端项目目录执行 npm run build）
COPY dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
