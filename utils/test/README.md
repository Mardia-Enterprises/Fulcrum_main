# S3Helper Test Suite

This directory contains tests and example usage for the `S3Helper` utility in the parent directory.

## Method Naming Convention

All S3-related methods in the `S3Helper` class use the `s3_` prefix (e.g., `s3_upload_file`, `s3_download_file`, etc.) to clearly identify them as S3 operations. This naming convention allows the class to be extended with methods for other AWS services in the future.

## Setup

Before running the tests or examples, ensure you have installed the required packages:

```bash
pip install boto3 python-dotenv
```

## Running Tests

The test suite uses Python's built-in `unittest` framework and mocks the AWS S3 API calls, so you can run the tests without actual AWS credentials or network access.

To run the tests:

```bash
python -m unittest test_cloud_helper.py
```

## Example Usage

The `example_usage.py` script demonstrates how to use the `S3Helper` class for common S3 operations. This script will attempt to connect to AWS S3 using the credentials defined in your `.env` file, so make sure your AWS credentials are properly configured.

To run the examples:

```bash
python example_usage.py
```

The examples showcase:

1. Uploading a single file to S3 with `s3_upload_file`
2. Uploading multiple files to S3 with `s3_upload_files`
3. Listing objects in an S3 bucket with `s3_list_objects`
4. Downloading a file from S3 with `s3_download_file`
5. Generating a presigned URL for an S3 object with `s3_generate_presigned_url`
6. Copying an object within S3 with `s3_copy_object`
7. Deleting an object from S3 with `s3_delete_object`

## Environment Variables

Make sure your `.env` file in the project root contains the following AWS-related variables:

```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
S3_BUCKET_NAME=your_bucket_name
S3_FOLDER_PATH=optional_folder_path
```

The `S3Helper` class will automatically load these variables from the `.env` file. 