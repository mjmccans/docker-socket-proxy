# mjmccans/docker-socket-proxy

This is a reverse proxy for your Docker socket that allows you to control what Docker API endpoints can be accessed by docker clients such as Portainer, Diun and Watchtower.

Using a proxy is important from a security perspective because giving direct access to your Docker socket essentially means giving root access to your host, and also could allow undesired changes to your other Docker containers and Docker environment.

## Inner Workings

This Docker image is based upon the official [Nginx Alpine](https://hub.docker.com/_/nginx) image with a small Python script that creates a nginx.conf file based upon environment labels you set when you run the image. By default certain read-only api commands are allowed (see below for more details), but you can adjust this to suit your needs. Where access to a certain API command has been revoked, an HTTP 403 Forbidden status is returned and there is an option that allows you to include additional details in the message (see below for more details).

## Security Warnings and Recommendations

- Never expose this container's port to a public network as this would allow anyone to connect to port and issue allowed docker commands. This container is intended to only be exposed on the internal Docker network of the service that will use the proxy.
- Only allow access to those API commands the service requires. One way to do this is to start with the default configuration, watch the logs (see below for more information), and only add those API commands that are necessary.

## Usage

1.  Run the container using a command similar to the following (Note: You may need the `--privileged` flag due to SELinux/AppArmor, but try it without first):

        $ docker container run \
            -d --privileged \
            --name docker-proxy \
            -e CONTAINERS=1 \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -p 127.0.0.1:2375:2375 \
            mjmccans/docker-socket-proxy

1.  You can list running containers because we set the `CONTAINERS=1` environment variable:

        $ docker -H localhost:2375 container ls
          CONTAINER ID   IMAGE                          COMMAND                  CREATED         STATUS         PORTS                              NAMES
          4f828bbd0dcc   mjmccans/docker-socket-proxy   "/docker-entrypoint.…"   2 minutes ago   Up 2 minutes   80/tcp, 127.0.0.1:2375->2375/tcp   docker-proxy

1.  However, you cannot list images because we did not override the default `IMAGES=0` environment label:

        $ docker -H localhost:2375 image ls
        Error response from daemon: 403 Forbidden: docker-socket-proxy is configured to not allow access to this function. To enable this function turn on the IMAGES option.

See the [examples](./examples) folder for some docker compose examples.

## Log Files / Return Messages

The container provides useful log output showing what api calls have been made, the return code and some additional detail that can be helpful for debugging. You can turn on the `DESCRIPTIVE_ERRORS` option to get more descriptive logging and client-side messages where a request is rejected.

### Example

In the example below, we can see that the first call to `info` has been accepted (return code 200) and the call to `volumes\create` has been rejected (return code 403). In addition, the last part of each line shows what environment variable option was in play to create this outcome. Note that if you do not have the `DESCRIPTIVE_ERRORS` option enabled you will not be given a specific environment variable option where a requires is rejected.

```
[25/Jan/2023:15:25:12 -0500] "GET /info HTTP/1.1" 200 [Location: INFO]
[25/Jan/2023:15:25:16 -0500] "POST /volumes/create HTTP/1.1" 403 [Location: VOLUMES_CREATE (BLOCKED)]
```

On the client side you can also get helpful information. With the `DESCRIPTIVE_ERRORS` option enabled you would get the following return message on the client side:
```
403 Forbidden: docker-socket-proxy is configured to not allow access to this function. To enable this function turn on the VOLUMES_CREATE option.
```

Without the `DESCRIPTIVE_ERRORS` option enabled you would get a more generic return message on the client like like the following:
```
403 Forbidden: docker-socket-proxy is configured to not allow access to this function.
```

## Options

Granting or revoking access to certain Docker API calls is done by setting environment variables, and the environment variables generally match the Docker API command they relate to. 

To grant or revoke access set the corresponding environment variable as follows:

- `0` to **revoke** access.
- `1` to **grant** access.

Below is a list of all of the options and each has a link to the Docker API Specification document so you can understand what each does.

### Granted by Default

By default, the following options are set (and you can more details on each below):

- `DESCRIPTIVE_ERRORS`
- `EVENTS`
- `PING`
- `VERSION`  

### All Options

#### Logging and Output

- `DESCRIPTIVE_ERRORS`: Add description %%%

#### GET Commands (Read-Only)

- [CONFIGS](https://docs.docker.com/engine/api/v1.41/#tag/Config)
- [CONTAINERS](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerCreate): Allows access to all GET commands for containers (e.g., list, inspect, logs, etc.)
- [EVENTS](https://docs.docker.com/engine/api/v1.41/#tag/System/operation/SystemEvents)
- [IMAGES](https://docs.docker.com/engine/api/v1.41/#tag/Image): Allows access to all GET commands for images (e.g., list, inspect, history, etc.)
- [INFO](https://docs.docker.com/engine/api/v1.41/#tag/System/operation/SystemInfo)
- [NETWORKS](https://docs.docker.com/engine/api/v1.41/#tag/Network): Allows access to all GET commands for networks (e.g., list, inspect, etc.)
- [PING](https://docs.docker.com/engine/api/v1.41/#tag/System/operation/SystemPing)
- [PLUGINS](https://docs.docker.com/engine/api/v1.41/#tag/Plugin): Allows access to all GET commands for plugins (e.g., list, get privileges, inspect, etc.)
- [SECRETS](https://docs.docker.com/engine/api/v1.41/#tag/Secret): Allows access to all GET commands for secrets (e.g., list, inspect, etc.)
- [SERVICES](https://docs.docker.com/engine/api/v1.41/#tag/Service): Allows access to all GET commands for services (e.g., list, inspect, logs, etc.)
- [SWARM](https://docs.docker.com/engine/api/v1.41/#tag/Swarm): Allows access to all GET commands for swarm (e.g., inspect, unlock key, etc.)
- [SYSTEM](https://docs.docker.com/engine/api/v1.41/#tag/System/operation/SystemDataUsage)
- [TASKS](https://docs.docker.com/engine/api/v1.41/#tag/Task): Allows access to all GET commands for tasks (e.g., list, inspect, etc.)
- [VERSION](https://docs.docker.com/engine/api/v1.41/#tag/System/operation/SystemVersion)
- [VOLUMES](https://docs.docker.com/engine/api/v1.41/#tag/Volume): Allows access to all GET commands for volumes (e.g., list, inspect, etc.)

#### POST Commands

- [AUTH](https://docs.docker.com/engine/api/v1.41/#section/Authentication)
- [CONTAINERS_ATTACH](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerAttach)
- [CONTAINERS_CREATE](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerCreate)
- [CONTAINERS_KILL](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerKill)
- [CONTAINERS_PAUSE](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerPause)
- [CONTAINERS_PRUNE](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerPrune)
- [CONTAINERS_RENAME](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerRename)
- [CONTAINERS_RESTART](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerRestart)
- [CONTAINERS_RESIZE](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerResize)
- [CONTAINERS_START](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerStart)
- [CONTAINERS_STOP](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerStop)
- [CONTAINERS_UPDATE](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerUpdate)
- [CONTAINERS_UNPAUSE](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerUnpause)
- [CONTAINERS_WAIT](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerWait)
- [CONTAINERS_EXEC](https://docs.docker.com/engine/api/v1.41/#tag/Exec/operation/ContainerExec)
- [DISTRIBUTION](https://docs.docker.com/engine/api/v1.41/#tag/Distribution)
- [EXEC](https://docs.docker.com/engine/api/v1.41/#tag/Exec/operation/ContainerExec): Allows access to all GET and POST commands for exec (e.g. start, resize, etc.)
- [IMAGES_BUILD](https://docs.docker.com/engine/api/v1.41/#tag/Image/operation/ImageBuild)
- [IMAGES_CREATE](https://docs.docker.com/engine/api/v1.41/#tag/Image/operation/ImageCreate)
- [IMAGES_PRUNE](https://docs.docker.com/engine/api/v1.41/#tag/Image/operation/ImagePrune)
- [NETWORKS_CONNECT](https://docs.docker.com/engine/api/v1.41/#tag/Network/operation/NetworkConnect)
- [NETWORKS_CREATE](https://docs.docker.com/engine/api/v1.41/#tag/Network/operation/NetworkCreate)
- [NETWORKS_DISCONNECT](https://docs.docker.com/engine/api/v1.41/#tag/Network/operation/NetworkDisconnect)
- [NETWORKS_PRUNE](https://docs.docker.com/engine/api/v1.41/#tag/Network/operation/NetworkPrune)
- [NODES](https://docs.docker.com/engine/api/v1.41/#tag/Node): Allows access to all GET and POST commands for nodes (e.g. list, inspect, update, etc.)
- [SESSION](https://docs.docker.com/engine/api/v1.41/#tag/Session)
- [VOLUMES_CREATE](https://docs.docker.com/engine/api/v1.41/#tag/Volume/operation/VolumeCreate)
- [VOLUMES_PRUNE](https://docs.docker.com/engine/api/v1.41/#tag/Volume/operation/VolumePrune)

#### Delete Commands

- [CONTAINERS_DELETE](https://docs.docker.com/engine/api/v1.41/#tag/Container/operation/ContainerDelete)
- [IMAGES_DELETE](https://docs.docker.com/engine/api/v1.41/#tag/Image/operation/ImageDelete)
- [NETWORKS_DELETE](https://docs.docker.com/engine/api/v1.41/#tag/Network/operation/NetworkDelete)
- [NODES_DELETE](https://docs.docker.com/engine/api/v1.41/#tag/Node/operation/NodeDelete)
- [VOLUMES_DELETE](https://docs.docker.com/engine/api/v1.41/#tag/Volume/operation/VolumeDelete)

## Inspiration

This project was inspired by [tecnativa/docker-socket-proxy](https://github.com/Tecnativa/docker-socket-proxy) and [fluencelabs/docker-socket-proxy](https://github.com/fluencelabs/docker-socket-proxy). Both of those projects build upon haproxy while I am more familiar (but by no means an expert) with Nginx so I have used that for this project. I also wanted to include a finer level of control as included in fluencelabs' project, and include more detailed log details and client messages to assist with setup.