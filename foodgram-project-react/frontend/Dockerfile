# build env
FROM node:13.12.0-alpine as build
WORKDIR /app
COPY ./frontend/package*.json ./
RUN npm install
COPY ./frontend/ ./
COPY ./infra/.env ./
RUN npm run build
CMD rm -rf result_build/build && cp -r build result_build
