# Static hosting for the site (Railway / any Docker host).
# The design-component runtime (support.js) evaluates its component logic with
# new Function(), so the Content-Security-Policy set in nginx.conf.template must
# allow 'unsafe-eval' or the shared header, nav, and dynamic bits won't render.
FROM nginx:alpine

# Only substitute ${PORT} in the template; leave nginx vars like $uri alone.
ENV NGINX_ENVSUBST_FILTER=PORT
# Default port so `listen ${PORT};` is always valid. Railway overrides PORT at runtime.
ENV PORT=8080

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY . /usr/share/nginx/html
# The nginx config template gets copied into the web root by "COPY ."; drop it.
RUN rm -f /usr/share/nginx/html/nginx.conf.template

EXPOSE 8080
