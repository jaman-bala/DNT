#!/bin/sh
# Builds the SeaweedFS S3 identity config from the same credentials the Django
# app uses: Docker secrets /run/secrets/aws_s3_access_key_id and
# /run/secrets/aws_s3_secret_access_key or, if absent, the AWS_S3_ACCESS_KEY_ID /
# AWS_S3_SECRET_ACCESS_KEY env vars — then hands off to the image entrypoint.
# Without -s3.config SeaweedFS would accept anonymous S3 requests.
set -eu

secret() {
  file="/run/secrets/$(printf '%s' "$1" | tr 'A-Z' 'a-z')"
  if [ -f "$file" ]; then
    tr -d '\r\n' < "$file"
  else
    printenv "$1" || true
  fi
}

ACCESS_KEY=$(secret AWS_S3_ACCESS_KEY_ID)
SECRET_KEY=$(secret AWS_S3_SECRET_ACCESS_KEY)

if [ -z "$ACCESS_KEY" ] || [ -z "$SECRET_KEY" ]; then
  echo "seaweedfs: AWS_S3_ACCESS_KEY_ID and AWS_S3_SECRET_ACCESS_KEY are required" >&2
  exit 1
fi
case "$ACCESS_KEY$SECRET_KEY" in
  *'"'* | *'\'*)
    echo 'seaweedfs: keys must not contain " or \' >&2
    exit 1
    ;;
esac

CONFIG=/tmp/s3.json
umask 077
cat > "$CONFIG" <<JSON
{
  "identities": [
    {
      "name": "app",
      "credentials": [{"accessKey": "$ACCESS_KEY", "secretKey": "$SECRET_KEY"}],
      "actions": ["Admin", "Read", "List", "Tagging", "Write"]
    }
  ]
}
JSON
# The image entrypoint drops privileges to the "seaweed" user.
if [ "$(id -u)" = "0" ]; then
  chown seaweed:seaweed "$CONFIG"
fi

exec /entrypoint.sh "$@" -s3.config="$CONFIG"
