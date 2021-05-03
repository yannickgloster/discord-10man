# Install dependencies stage
FROM node:15-alpine as install

WORKDIR /usr/src/app

COPY prisma ./prisma
COPY .env package-lock.json package.json ./

RUN npm install
RUN npx prisma generate
RUN npx prisma migrate dev

# Run stage
FROM node:15-alpine

WORKDIR /usr/src/app

COPY commands ./commands
COPY images ./images
COPY util ./util
COPY .env .eslintrc.json bot.js config.json package-lock.json package.json ./
COPY --from=install /usr/src/app/node_modules ./node_modules
COPY --from=install /usr/src/app/prisma ./prisma

RUN apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--"]

CMD ["npm", "run", "start"]