from io import BytesIO
def stream_to_minio(file, minio_client, bucket_name,metadata, object_key):
    """
    Stream PDF data to MinIO using BytesIO buffer
    """
    file.stream.seek(0)
    
    file_content = file.read()
    file_size = len(file_content)
    file.stream.seek(0)
    
    if file_size < 5 * 1024 * 1024: 
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_key,
            data=BytesIO(file_content),
            length=file_size,
            content_type='application/pdf',
        )
    else:
        # Multipart upload for larger files
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=object_key,
            data=file.stream,
            length=-1,  # Unknown size
            part_size=10 * 1024 * 1024,  # Use 10 MB parts
            content_type='application/pdf',
        )
    
