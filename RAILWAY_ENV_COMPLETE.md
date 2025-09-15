# Complete Railway Environment Variables

## 🗄️ **Backend Service Environment Variables**

Copy these **EXACT** variable names and values into Railway:

### **Database (Railway Auto-Provided)**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### **Environment Settings**
```bash
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0  
API_PORT=$PORT
```

### **CORS Origins (Update after frontend deploys)**
```bash
ALLOWED_ORIGINS=https://your-frontend-url.up.railway.app,https://vantage-frontend-production.up.railway.app
```

### **Authentication - Clerk (Your Real Keys)**
```bash
CLERK_PUBLISHABLE_KEY=pk_live_your_real_publishable_key_here
CLERK_SECRET_KEY=sk_live_your_real_secret_key_here
```

### **Satellite API (Your Real Credentials)**
```bash
CLIENT_ID=your_real_satellite_client_id
CLIENT_SECRET=your_real_satellite_client_secret
```

### **AWS S3 Configuration (Your Real AWS Credentials)**
```bash
AWS_ACCESS_KEY_ID=your_real_aws_access_key
AWS_SECRET_ACCESS_KEY=your_real_aws_secret_key
AWS_S3_REGION=us-east-1
AWS_S3_BUCKET=thevantage
S3_UPLOAD_ENABLED=true
```

### **Image Processing**
```bash
USE_OPENCV=true
IMAGES_DIR=/app/images
```

---

## 🎨 **Frontend Service Environment Variables**

### **API Configuration (Update with your backend URL)**
```bash
REACT_APP_API_URL=https://your-backend-service.up.railway.app
```

### **Authentication**
```bash
REACT_APP_CLERK_PUBLISHABLE_KEY=pk_live_your_real_publishable_key_here
```

### **Environment**
```bash
REACT_APP_ENVIRONMENT=production
```

---

## 📝 **Variable Checklist**

### ✅ **Backend Must Have (15 variables):**
- [ ] `DATABASE_URL` (Railway auto-provides)
- [ ] `ENVIRONMENT` 
- [ ] `DEBUG`
- [ ] `API_HOST`
- [ ] `API_PORT` 
- [ ] `ALLOWED_ORIGINS`
- [ ] `CLERK_PUBLISHABLE_KEY`
- [ ] `CLERK_SECRET_KEY`
- [ ] `CLIENT_ID`
- [ ] `CLIENT_SECRET`
- [ ] `AWS_ACCESS_KEY_ID`
- [ ] `AWS_SECRET_ACCESS_KEY`
- [ ] `AWS_S3_REGION`
- [ ] `AWS_S3_BUCKET`
- [ ] `S3_UPLOAD_ENABLED`
- [ ] `USE_OPENCV`
- [ ] `IMAGES_DIR`

### ✅ **Frontend Must Have (3 variables):**
- [ ] `REACT_APP_API_URL`
- [ ] `REACT_APP_CLERK_PUBLISHABLE_KEY`
- [ ] `REACT_APP_ENVIRONMENT`

---

## 🔧 **Railway Setup Order**

1. **Deploy Backend** with all variables above
2. **Add PostgreSQL Database** (provides DATABASE_URL automatically)
3. **Deploy Frontend** with variables above
4. **Update ALLOWED_ORIGINS** in backend with frontend URL
5. **Test the connection**

---

## 🚨 **Common Issues & Fixes**

### **Backend Won't Start:**
- Missing required environment variables
- Check Railway logs for specific missing vars

### **Database Connection Failed:**
- Ensure PostgreSQL service is added to project
- DATABASE_URL should auto-populate

### **Frontend Can't Connect:**
- Check REACT_APP_API_URL points to backend service
- Verify CORS settings in ALLOWED_ORIGINS

### **S3 Upload Errors:**
- Verify AWS credentials are correct
- Check S3 bucket permissions