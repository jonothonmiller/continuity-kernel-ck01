FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY src ./src
USER node
ENV PORT=3000 CK01_DATABASE_PATH=/tmp/ck01-adapter.sqlite
EXPOSE 3000
CMD ["npm","start"]
