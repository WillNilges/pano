#!/bin/bash

BUCKET=panoramas
THUMB_BUCKET=thumbs
KEY_NAME=pano-app-key

pano_garage="podman exec -it pano-dev_garage_1 /garage"

node_id=$($pano_garage status | tail -n 1 | awk '{print $1}')
$pano_garage layout assign -z dc1 -c 1G $node_id
$pano_garage layout apply --version 1
$pano_garage bucket create $BUCKET 
$pano_garage bucket create $THUMB_BUCKET 

# check for existing key
$pano_garage key list | grep $KEY_NAME
if [[ $? -ne 0 ]]; then
		echo Key not found. Creating key.
		$pano_garage key create $KEY_NAME
fi

$pano_garage bucket allow --read --write --owner $BUCKET --key $KEY_NAME
$pano_garage bucket allow --read --write --owner $THUMB_BUCKET --key $KEY_NAME

echo '=== Done! ==='
echo 'Paste the Key ID and Secret key into your .env as GARAGE_API_KEY and GARAGE_SECRET'
