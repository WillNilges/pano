FROM minio/minio
CMD ["server", "/data", "--address=0.0.0.0:9000"]
