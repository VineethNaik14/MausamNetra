# MausamNetra frontend — runs the Vite dev server (matches `npm run dev`
# from frontend/README.md). For production, swap for a multi-stage
# build + nginx serve of `dist/` instead.
FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]