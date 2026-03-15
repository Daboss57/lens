FROM node:20-alpine AS build

WORKDIR /app

COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci

COPY dashboard .
ARG VITE_LENS_API_URL=http://localhost:8100
ENV VITE_LENS_API_URL=$VITE_LENS_API_URL
RUN npm run build

FROM nginx:1.27-alpine

COPY dashboard/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 4200
