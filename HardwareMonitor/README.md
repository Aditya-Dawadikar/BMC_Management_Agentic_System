# Server to expose Hardware Metrics

This server is dependent on `RedFishMockup` Server.

### Installation

Install the dependencies
```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Quick Start

Run this server using the following command
```
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Feel free to modify the `update_metrics()` logic to get device specific information.

### Environment Setup

Create a `.env` file with the following environment variables. AWS related credentials are secret, request for access.

| Environment Variable      | Description | Value |
| ----------- | ----------- | ----------- |
| S3_BUCKET_NAME      | Name of the S3 bucket where files to be archived       | axiado-bmc |
| AWS_ACCESS_KEY_ID   | AWS access key        | Request for Keys |
|AWS_SECRET_ACCESS_KEY| AWS secret access key | Request for Keys |
|AWS_DEFAULT_REGION| AWS region | us-east-2 |
|PROBE_INTERVAL| Probe hardware very `n` seconds | 2 |
|MONGO_DB_NAME| your db name | bmc_telemetry_db |
|MONGO_COLLECTION_NAME| collection name | s3_telemetry_batches |
|MONGO_URI| Mongo db uri | mongodb://localhost:27017/ |
|REDFISH_BASE_URL| RedFish Mock Server URL|http://localhost:8001/redfish/v1|

### Important Note

The logic for archiving data to S3 and Mongodb is diasbled by default, please uncomment this code in `main.py`

```
    # TODO: enable this when data upload is needed
    # s3.put_object(
    #     Bucket=s3_bucket_name,
    #     Key=filename,
    #     Body=json.dumps(s3_buffer).encode("utf-8"),
    #     ContentType="application/json"
    # )
    # mongo_collection.insert_one(summary_doc)

```