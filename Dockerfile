FROM nginx:1.27.4-alpine AS stage1

# Expose port 2375
EXPOSE 2375

# Set environment var defaults
ENV DESCRIPTIVE_ERRORS=1 \
    # ALLOW_RESTARTS=0 \
    AUTH=0 \
    COMMIT=0 \ 
    CONFIGS=0 \
    CONTAINERS=0 \
    CONTAINERS_ATTACH=0 \
    CONTAINERS_CREATE=0 \
    CONTAINERS_DELETE=0 \
    CONTAINERS_KILL=0 \
    CONTAINERS_PAUSE=0 \
    CONTAINERS_PRUNE=0 \
    CONTAINERS_RENAME=0 \
    CONTAINERS_RESTART=0 \
    CONTAINERS_RESIZE=0 \
    CONTAINERS_START=0 \
    CONTAINERS_STOP=0 \
    CONTAINERS_UPDATE=0 \
    CONTAINERS_UNPAUSE=0 \
    CONTAINERS_WAIT=0 \
    CONTAINERS_EXEC=0 \
    DISTRIBUTION=0 \
    EVENTS=1 \
    EXEC=0 \
    IMAGES=0 \
    IMAGES_BUILD=0 \
    IMAGES_CREATE=0 \
    IMAGES_DELETE=0 \
    IMAGES_PRUNE=0 \
    INFO=0 \
    NETWORKS=0 \
    NETWORKS_CONNECT=0 \
    NETWORKS_CREATE=0 \
    NETWORKS_DISCONNECT=0 \
    NETWORKS_DELETE=0 \
    NETWORKS_PRUNE=0 \
    NODES=0 \
    NODES_DELETE=0 \
    PING=1 \
    PLUGINS=0 \
    SECRETS=0 \
    SERVICES=0 \
    SESSION=0 \
    SWARM=0 \
    SYSTEM=0 \
    TASKS=0 \
    VERSION=1 \
    VOLUMES=0 \
    VOLUMES_CREATE=0 \
    VOLUMES_PRUNE=0 \
    VOLUMES_DELETE=0

# Install python
RUN apk add --update --no-cache python3

# Copy files
COPY --chmod=775 docker-proxy-config.py /docker-entrypoint.d/10-docker-proxy-config.sh
