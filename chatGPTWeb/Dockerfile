FROM node:latest
WORKDIR /webapp
COPY . .
RUN npm install
EXPOSE 4300
RUN npm run build
# Serve the application using a simple static file server
# Use `serve` package to serve the production build
RUN npm install -g serve

CMD ["serve", "-s", "dist", "-l", "4300"]

#CMD ./script.sh

 #docker build -t web:2 .
 #docker container run -p 4200:4200 -it web:2



