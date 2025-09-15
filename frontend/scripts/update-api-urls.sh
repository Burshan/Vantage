#!/bin/bash
# Update hardcoded API URLs in frontend
# This script replaces localhost:5000 with environment-aware API configuration

echo "🔄 Updating hardcoded API URLs in frontend..."

# Create config directory if it doesn't exist
mkdir -p src/config

# List files that need updating
echo "📋 Files with hardcoded localhost:5000:"
grep -r "localhost:5000" src/ --include="*.js" --include="*.jsx" | cut -d: -f1 | sort | uniq

echo ""
echo "🔄 Processing updates..."

# Update AnalysisResultsTab.js
if [ -f "src/components/dashboard/AnalysisResultsTab.js" ]; then
    echo "  📄 Updating AnalysisResultsTab.js"
    
    # Add import at the top
    sed -i '' '1i\
import { buildImageURL } from "../../config/api";
' src/components/dashboard/AnalysisResultsTab.js
    
    # Replace hardcoded URLs
    sed -i '' 's|http://localhost:5000\${|buildImageURL(|g' src/components/dashboard/AnalysisResultsTab.js
    sed -i '' 's|\${analysisResults\.images\.\([^.]*\)\.url}|analysisResults.images.\1.url.replace("/api/image/", ""))|g' src/components/dashboard/AnalysisResultsTab.js
fi

echo "✅ API URL updates completed!"
echo ""
echo "📋 Remaining hardcoded URLs (if any):"
grep -r "localhost:5000" src/ --include="*.js" --include="*.jsx" | wc -l | xargs echo "Count:"

echo ""
echo "🎯 Next steps:"
echo "1. Test the application: npm start"
echo "2. Verify API calls work correctly"
echo "3. Set REACT_APP_API_URL for production deployment"