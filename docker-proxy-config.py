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

# Setup variables (the order matters from an nginx perspective)
VARS = {
    # GET Requests
    "AUTH": {"type": "GET", "regex": "auth"},
    "BUILD": {"type": "GET", "regex": "build"},
    "COMMIT": {"type": "GET", "regex": "commit"},
    "CONFIGS": {"type": "GET", "regex": "configs"},
    # Container commands
    "CONTAINERS_CREATE": {"type": "POST", "regex": "containers/create"},
    "CONTAINERS_PRUNE": {"type": "POST", "regex": "containers/prune"},
    "ALLOW_RESTARTS": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/((stop)|(restart)|(kill))"},
    "CONTAINERS_RESIZE": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/resize"},
    "CONTAINERS_START": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/start"},
    "CONTAINERS_UPDATE": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/update"},
    "CONTAINERS_RENAME": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/rename"},
    "CONTAINERS_PAUSE": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/pause"},
    "CONTAINERS_UNPAUSE": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/unpause"},
    "CONTAINERS_ATTACH": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/attach"},
    "CONTAINERS_WAIT": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/wait"},
    "CONTAINERS_EXEC": {"type": "POST", "regex": "containers/[a-zA-Z0-9_.-]+/exec"},
    # "CONTAINERS_DELETE": {"type": "DELETE", "regex": "containers/[a-zA-Z0-9_.-]+"},
    "CONTAINERS": {"type": "GET", "regex": "containers"},
    # End Container commands
    "DISTRIBUTION": {"type": "GET", "regex": "distribution"},
    "EVENTS": {"type": "GET", "regex": "events"},
    # %%% LOOK INTO WHETHER THIS IS POST, GET OR BOTH
    "EXEC": {"type": "POST GET", "regex": "exec"},
    # Images commands
    "IMAGES_CREATE": {"type": "POST", "regex": "images/create"},
    "IMAGES_PRUNE": {"type": "POST", "regex": "images/prune"},
    # "IMAGES_DELETE": {"type": "DELETE", "regex": "images/[a-zA-Z0-9_.-]+"},
    "IMAGES": {"type": "GET", "regex": "images"},
    # End Images commands
    "INFO": {"type": "GET", "regex": "info"},
    # Network Commands
    "NETWORKS_CREATE": {"type": "POST", "regex": "networks/create"},
    "NETWORKS_PRUNE": {"type": "POST", "regex": "networks/prune"},
    # "NETWORKS_DELETE": {"type": "DELETE", "regex": "networks/[a-zA-Z0-9_.-]+"},
    "NETWORKS": {"type": "GET", "regex": "networks"},
    # End Network Commands
    "NODES": {"type": "GET", "regex": "nodes"},
    "PING": {"type": "GET", "regex": "_ping"},
    "PLUGINS": {"type": "GET", "regex": "plugins"},
    "POST": {"type": "GET", "regex": "post"},
    "SECRETS": {"type": "GET", "regex": "secrets"},
    "SERVICES": {"type": "GET", "regex": "services"},
    "SESSION": {"type": "GET", "regex": "session"},
    "SWARM": {"type": "GET", "regex": "swarm"},
    "SYSTEM": {"type": "GET", "regex": "system"},
    "TASKS": {"type": "GET", "regex": "tasks"},
    "VERSION": {"type": "GET", "regex": "version"},
    # Volume commands
    "VOLUMES_CREATE": {"type": "POST", "regex": "volumes/create"},
    "VOLUMES_PRUNE": {"type": "POST", "regex": "volumes/prune"},
    # "VOLUMES_DELETE": {"type": "DELETE", "regex": "volumes/[a-zA-Z0-9_.-]+"},
    "VOLUMES": {"type": "GET", "regex": "volumes"}
    # End volume commands
}

# Create custom errors directory and default 403 error file
os.makedirs("/usr/share/nginx/html/error", exist_ok=True)
e = open(f"/usr/share/nginx/html/error/custom_403.html", "w")
e.write(f'403 Forbidden: docker-socket-proxy is configured to not allow access to this function.')
e.close()

# Open config file
f = open("/etc/nginx/nginx.conf", "w")

# Output generic nignx.conf content, but have workers run as root so they can access the docker socket.
f.write('''
user root root; # Workers need root access to access to docker socket.
error_log  /var/log/nginx/error.log notice;
pid        /var/run/nginx.pid;

events {
    worker_connections  1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
    #                   '$status $body_bytes_sent "$http_referer" '
    #                   '"$http_user_agent" "$http_x_forwarded_for"';
    log_format  main  '[$time_local] "$request" $status';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    #tcp_nopush     on;

    keepalive_timeout  65;

    #gzip  on;

    server {
        listen 2375 default_server;

        # Custom 403 forbidden page
        error_page 403 /error/custom_403.html;
        location /error {
            root /usr/share/nginx/html;
            internal;
        }
        
        # deny everything that doesn't match another location
        location / {
            return 403; 
        }

''')

# Output the relevant locations
for key in VARS:
    # Only add location if enviroment label set.
    if (os.environ.get(key) == "1"):
        # Check if type is DELETE is also set (fixes issues with priority of regex)
        
        if (os.environ.get(key+"_DELETE") == "1"):
            type = VARS[key]['type'] + " DELETE"
        else:
            type = VARS[key]['type']

        # Output location block
        f.writelines([
            f"        # {key}\n",
            f"        location ~ ^(/v[\d\.]+)?/{VARS[key]['regex']} {{\n",
            "            proxy_pass http://docker;\n",
            # Added to enable websockets
            "            proxy_http_version 1.1;\n",
            # "            proxy_set_header Connection '';\n"
            "            proxy_set_header Upgrade $http_upgrade;\n",
            # "            proxy_set_header Connection 'Upgrade';\n",
            "            proxy_set_header Connection $http_connection;\n",
            f"            limit_except {type} DELETE {{\n",
            "                deny all;\n",
            "            }\n",
            "        }\n",
            "\n"
        ])
    elif (os.environ.get("DESCRIPTIVE_ERRORS") == "1"):
        # Output location block for descriptive errors
        f.writelines([
            f"        # {key} forbidden\n",
            f"        location ~ ^(/v[\d\.]+)?/{VARS[key]['regex']} {{\n",
            "           # Custom 403 forbidden page\n",
            f"           error_page 403 /error/custom_403_{key}.html;\n",
            "           return 403;\n",
            "        }\n",
            "\n"
        ])

        # Output the custom error page
        e = open(f"/usr/share/nginx/html/error/custom_403_{key}.html", "w")
        e.write(f'403 Forbidden: docker-socket-proxy is configured to not allow access to this function. To enable this function turn on the {key} option.')
        e.close()

# Output closing text
f.write('''
    }

    upstream docker {
        server unix:/var/run/docker.sock;
        # keepalive 64;
    }
}
''')

f.close()
