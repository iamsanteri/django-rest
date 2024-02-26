# !/bin/sh

set -e # Will exit if any command fails

# Replace environment variables in the template file
envsubst < /etc/nginx/default.conf.tpl > /etc/nginx/conf.d/default.conf

# Start nginx
nginx -g 'daemon off;'