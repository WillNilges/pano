#!/bin/bash

BUCKET=panoramas

pano_garage="podman exec -it pano-dev_garage_1 /garage"

node_id=$($pano_garage status | tail -n 1 | awk '{print $1}')
$pano_garage layout assign -z dc1 -c 1G $node_id
$pano_garage layout apply --version 1
$pano_garage bucket create $BUCKET 
$pano_garage bucket info $BUCKET
$pano_garage key create pano-app-key
$pano_garage bucket allow --read --write --owner $BUCKET --key pano-app-key

echo '=== Done! ==='
echo 'Paste the Key ID and Secret key into your .env as GARAGE_API_KEY and GARAGE_SECRET'
