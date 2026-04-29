FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install --legacy-peer-deps

COPY . .

EXPOSE 5173

# Vite requires the --host flag to expose the port to the network
CMD ["npm", "run", "dev", "--", "--host"]
