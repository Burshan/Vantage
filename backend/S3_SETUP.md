# S3 Integration Setup Guide

## Overview
This guide will help you configure AWS S3 for satellite image storage in your Vantage application.

## Prerequisites
- AWS account with S3 access
- AWS CLI or IAM user with programmatic access
- Your S3 bucket created and configured

## Environment Variables

Add the following variables to your `.env` file in the backend directory:

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_access_key_here
AWS_S3_REGION=us-east-1
AWS_S3_BUCKET=your_bucket_name_here
S3_UPLOAD_ENABLED=true
```

## S3 Bucket Setup

### 1. Create S3 Bucket
```bash
aws s3 mb s3://your-vantage-satellite-images-bucket --region us-east-1
```

### 2. Configure Bucket Policy (Optional - for public read access)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-vantage-satellite-images-bucket/*"
        }
    ]
}
```

### 3. Configure CORS (for frontend access)
```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "HEAD"],
        "AllowedOrigins": ["http://localhost:3000", "https://your-domain.com"],
        "ExposeHeaders": [],
        "MaxAgeSeconds": 3000
    }
]
```

## IAM Policy

Create an IAM user with the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket",
                "s3:PutObjectAcl",
                "s3:PutBucketLifecycleConfiguration",
                "s3:GetBucketLifecycleConfiguration"
            ],
            "Resource": [
                "arn:aws:s3:::your-vantage-satellite-images-bucket",
                "arn:aws:s3:::your-vantage-satellite-images-bucket/*"
            ]
        }
    ]
}
```

## Folder Structure

The S3 service automatically organizes images in this structure:
```
your-bucket/
├── raw/
│   └── aoi_{id}/
│       └── YYYY-MM-DD/
│           └── filename.jpg
├── normalized/
│   └── aoi_{id}/
│       └── YYYY-MM-DD/
│           └── filename.jpg
└── heatmaps/
    └── aoi_{id}/
        └── YYYY-MM-DD/
            └── filename.jpg
```

## Lifecycle Policies

The system will automatically configure lifecycle policies:
- **raw/**: 30 days → Standard-IA, 90 days → Glacier, 365 days → Delete
- **normalized/**: 90 days → Standard-IA, 365 days → Delete  
- **heatmaps/**: 365 days → Delete

## Testing the Setup

1. Install dependencies:
```bash
pip install boto3 botocore
```

2. Test S3 connection:
```bash
python -c "from services.s3_service import s3_service; print(f'S3 enabled: {s3_service.enabled}')"
```

3. Check bucket access:
```bash
curl http://localhost:5000/api/image/upload-status
```

Expected response:
```json
{
  "s3_enabled": true,
  "bucket_name": "your-vantage-satellite-images-bucket",
  "region": "us-east-1"
}
```

## Integration Points

### 1. Image Upload
```python
from services.s3_service import s3_service
from PIL import Image

# Upload PIL image to S3
result = s3_service.upload_image(
    image=pil_image,
    file_type='heatmaps',  # 'raw', 'normalized', 'heatmaps'
    aoi_id='123',
    filename='analysis_result.jpg'
)

if result:
    s3_key = result['s3_key']
    # Store s3_key in database
```

### 2. Generate Signed URLs
```python
# Generate 1-hour signed URL
signed_url = s3_service.generate_signed_url(s3_key, expiration=3600)
```

### 3. Database Integration
The `AnalysisHistory` model now includes:
- `image1_s3_key`, `image2_s3_key`, `heatmap_s3_key` - S3 object keys
- `get_image_url()` method - Automatically returns S3 signed URL or local fallback

## Troubleshooting

### Common Issues

1. **"S3 not available" warning**
   - Check AWS credentials in .env file
   - Verify bucket exists and is accessible
   - Confirm IAM permissions

2. **"Failed to upload to S3"**
   - Check bucket policy and CORS configuration
   - Verify S3_UPLOAD_ENABLED=true
   - Check AWS region matches bucket region

3. **Images not loading in frontend**
   - Signed URLs expire after 1 hour by default
   - Check CORS configuration for frontend domain
   - Verify image URLs are being generated correctly

### Debug Commands

```bash
# Check S3 service status
python -c "from services.s3_service import s3_service; print(s3_service.get_storage_stats())"

# Test image upload
python -c "
from services.s3_service import s3_service
from PIL import Image
import tempfile

# Create test image
img = Image.new('RGB', (100, 100), 'red')
result = s3_service.upload_image(img, 'raw', 'test', 'test.jpg')
print(f'Upload result: {result}')
"
```

## Cost Optimization

- Images are automatically stored in Standard-IA after 30-90 days
- Old images are moved to Glacier or deleted based on lifecycle policies
- Use JPEG compression for smaller file sizes
- Consider bucket versioning policies for important data

## Security Notes

- Never commit AWS credentials to git
- Use IAM roles instead of access keys in production
- Consider enabling bucket encryption
- Review bucket policies regularly
- Monitor S3 access logs for unusual activity