#!/usr/bin/python3
#
# Copyright (c) 2023 Mark McCans
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os

# Setup variables (the order matters from an nginx location parsing perspective)
#
# Note: DELETE operations are handled as a special case due to how
#       the NGINX config file format.

VARS = {
    # GET Requests
    "AUTH": {"type": "POST", "regex": "auth"},
    "COMMIT": {"type": "GET", "regex": "commit"}, # %%% Look into this (seems images related only and appears to be a POST command)
    "CONFIGS": {"type": "GET", "regex": "configs"},
    # Container commands
    "CONTAINERS_ATTACH": {"type": "GET POST", "regex": "containers/[a-zA-Z0-9_.-]+/attach"},
    "CONTAINERS_KILL": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/kill"},
    "CONTAINERS_PAUSE": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/pause"},
    "CONTAINERS_RENAME": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/rename"},
    "CONTAINERS_RESTART": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/restart"},
    "CONTAINERS_RESIZE": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/resize"},
    "CONTAINERS_START": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/start"},
    "CONTAINERS_STOP": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/stop"},
    "CONTAINERS_UPDATE": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/update"},
    "CONTAINERS_UNPAUSE": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/unpause"},
    "CONTAINERS_WAIT": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/wait"},
    "CONTAINERS_EXEC": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/exec"},
    "CONTAINERS_CREATE": {"type": "POST", "regex": "containers/create"},
    "CONTAINERS_PRUNE": {"type": "POST", "regex": "containers/prune"},
    "CONTAINERS": {"type": "GET", "regex": "containers"},
    # End Container commands
    "DISTRIBUTION": {"type": "GET", "regex": "distribution"},
    "EVENTS": {"type": "GET", "regex": "events"},
    "EXEC": {"type": "POST GET", "regex": "exec"},
    # Images commands
    "IMAGES_BUILD": {"type": "GET", "regex": "build"},
    "IMAGES_CREATE": {"type": "POST", "regex": "images/create"},
    "IMAGES_PRUNE": {"type": "POST", "regex": "images/prune"},
    "IMAGES": {"type": "GET", "regex": "images"},
    # End Images commands
    "INFO": {"type": "GET", "regex": "info"},
    # Network Commands
    "NETWORKS_CONNECT": {"type": "POST", "regex": "networks/[a-zA-Z0-9_.-]+/connect"},
    "NETWORKS_CONNECT": {"type": "POST", "regex": "networks/[a-zA-Z0-9_.-]+/disconnect"},
    "NETWORKS_CREATE": {"type": "POST", "regex": "networks/create"},
    "NETWORKS_PRUNE": {"type": "POST", "regex": "networks/prune"},
    "NETWORKS": {"type": "GET", "regex": "networks"},
    # End Network Commands
    "NODES": {"type": "GET POST", "regex": "nodes"},
    "PING": {"type": "GET", "regex": "_ping"},
    "PLUGINS": {"type": "GET", "regex": "plugins"}, # There are more options
    "SECRETS": {"type": "GET", "regex": "secrets"}, # There are more options
    "SERVICES": {"type": "GET", "regex": "services"}, # There are more options
    "SESSION": {"type": "POST", "regex": "session"},
    "SWARM": {"type": "GET", "regex": "swarm"}, # There are more options
    "SYSTEM": {"type": "GET", "regex": "system"},
    "TASKS": {"type": "GET", "regex": "tasks"},
    "VERSION": {"type": "GET", "regex": "version"},
    # Volume commands
    "VOLUMES_CREATE": {"type": "POST", "regex": "volumes/create"},
    "VOLUMES_PRUNE": {"type": "POST", "regex": "volumes/prune"},
    "VOLUMES": {"type": "GET", "regex": "volumes"}
    # End volume commands
}

# Open config file
f = open("/etc/nginx/nginx.conf", "w")

# Output generic nignx.conf content, but have workers run as root so they can access the docker socket.
f.write('''user root root; # Workers need root access to access to docker socket.
error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '[$time_local] "$request" $status [$sent_http_docker_proxy_rule]';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    tcp_nodelay     on;
    #tcp_nopush     on;

    underscores_in_headers on;
    keepalive_timeout  65;

    #gzip  on;

    # Used below for websocket connections
    map $http_upgrade $connection_upgrade {
        default upgrade;
        '' close;
    }
    
    server {
        listen 2375 default_server;

        # Deny everything that doesn't match another location
        location / {
            add_header 'docker-proxy-rule' 'Location: Default (BLOCKED)' always;
            return 403 '403 Forbidden: docker-socket-proxy is configured to not allow access to this function.'; 
        }

''')

# Output the relevant locations
for key in VARS:
    # Only add location if enviroment label set.
    if (os.environ.get(key) == "1"):
        
        # Handle DELETE as a special case of the base GET command
        if (os.environ.get(key+"_DELETE") == "1"):
            type = VARS[key]['type'] + " DELETE"
        else:
            type = VARS[key]['type']

        # Output location block
        f.writelines([
            f"        # {key}\n",
            f"        location ~ ^(/v[\d\.]+)?/{VARS[key]['regex']} {{\n",
            f"            add_header 'docker-proxy-rule' 'Location: {key}' always;\n"
            "            proxy_pass http://docker;\n",
            # Bellow added to enable websockets (See https://www.nginx.com/blog/websocket-nginx/)
            "            proxy_http_version 1.1;\n",
            "            proxy_set_header Upgrade $http_upgrade;\n",
            "            proxy_set_header Connection $connection_upgrade;\n",
            "            proxy_set_header Host $host;\n",
            # End of websockets lines
            f"            limit_except {type} {{\n",
            "                deny all;\n",
            "            }\n",
            "        }\n",
            "\n"
        ])
    elif (os.environ.get("DESCRIPTIVE_ERRORS") == "1"):
        # Output location block for descriptive errors for forbidden locations
        f.writelines([
            f"        # {key} forbidden\n",
            f"        location ~ ^(/v[\d\.]+)?/{VARS[key]['regex']} {{\n",
            f"            add_header 'docker-proxy-rule' 'Location: {key} (BLOCKED)' always;\n"
            f"            return 403 '403 Forbidden: docker-socket-proxy is configured to not allow access to this function. To enable this function turn on the {key} option.';\n",
            "        }\n",
            "\n"
        ])

# Output closing text
f.write('''}

    upstream docker {
        server unix:/var/run/docker.sock;
        keepalive 32;
    }
}
''')

f.close()
