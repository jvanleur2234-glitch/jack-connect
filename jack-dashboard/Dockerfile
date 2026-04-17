FROM ghcr.io/gethomepage/homepage:latest

# Copy JackConnect custom config
COPY config/ /app/config/

# Environment variables
ENV HOMEPAGE_ALLOWED_HOSTS="localhost,127.0.0.1,*.zo.space"
ENV PUID=1000
ENV PGID=1000

# JackConnect-specific settings
ENV JACK_CONNECT_MODE=true

EXPOSE 3000

VOLUME /app/config
