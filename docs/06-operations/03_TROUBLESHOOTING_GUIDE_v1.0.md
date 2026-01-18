# Troubleshooting Guide v1.0

**Document**: Common Issues and Solutions  
**Version**: 1.0  
**Last Updated**: January 2026  
**Audience**: Operations Team, Support Staff, Users

---

## Overview

This guide helps diagnose and fix common issues in KraftdIntel. Use the symptoms to find your problem and follow the solution steps.

---

## User Issues

### Issue: "Cannot Sign Up - Invalid Email"

**Symptoms**:
- User sees red error: "Invalid email address"
- Can't complete registration
- Email format looks correct

**Possible Causes**:
1. Email field is empty
2. Email contains invalid characters
3. Email is already registered
4. Backend validation is stricter than frontend

**Solution**:
1. Clear email field and re-enter
2. Ensure no spaces before/after email
3. Use standard email format: user@example.com
4. Check for typos in domain
5. Try different email if registered

**Backend Check**:
```powershell
# Check validation rules
cd backend
.venv\Scripts\Activate.ps1
python -c "from models.user import UserRegister; 
          ur = UserRegister(email='test@example.com', password='Test123', 
                           acceptTerms=True, acceptPrivacy=True)
          print('Validation passed')"
```

---

### Issue: "Password Too Weak"

**Symptoms**:
- Red error: "Password does not meet requirements"
- Password looks strong enough
- Can't create account

**Requirements**:
- Minimum 8 characters
- Maximum 128 characters
- No spaces allowed
- No special character restrictions

**Solution**:
1. Remove any spaces from password
2. Ensure at least 8 characters
3. Use letters, numbers, optional: !@#$%^&*
4. Try: `SecurePass123` (confirmed working)

**Example**:
```
❌ "Pass 123"        (contains space)
❌ "Pass"            (too short)
✅ "SecurePass123"   (valid)
✅ "MyP@ssw0rd!"     (valid)
```

---

### Issue: "Login Failed - Invalid Credentials"

**Symptoms**:
- Can't sign in
- "Invalid email or password" message
- Just registered account
- Changed password recently

**Possible Causes**:
1. Wrong password typed
2. Caps Lock is on
3. Wrong email address
4. Account not created (registration failed silently)
5. Incorrect credentials

**Solution**:
1. **Try again slowly**:
   - Click "Clear All" if form has previous entries
   - Type email carefully
   - Type password carefully (check Caps Lock)
   - Click Sign In

2. **Reset password** (if you don't remember it):
   - Click "Forgot Password?"
   - Enter email
   - Check email for reset link
   - Set new password
   - Sign in with new password

3. **Verify account exists**:
   - Try registering again with same email
   - If "Email already registered" → account exists
   - Then try login again

4. **Check backend logs**:
   ```powershell
   # SSH to backend server
   tail -f backend_logs.txt
   # Look for authentication attempts
   ```

---

### Issue: "Session Expired - Please Login Again"

**Symptoms**:
- Working normally, then see login screen
- Message: "Your session has expired"
- Lost unsaved work
- Happens after ~60 minutes

**Why This Happens**:
- Access tokens expire after 60 minutes (by design)
- This is for security (in case token is stolen)
- Users with 7-day refresh tokens stay logged in

**Solution**:
1. Click "Login Again"
2. Email may be pre-filled
3. Enter password
4. Click Sign In
5. Redirected back to where you were

**Prevention**:
- Save work frequently (every 10-15 minutes)
- Or contact admin to extend token lifetime

---

### Issue: "Dashboard Won't Load - Blank Page"

**Symptoms**:
- Redirected to dashboard
- Page is blank/white
- No error messages
- "Loading..." spinner forever

**Possible Causes**:
1. Backend not running
2. Network connection issue
3. JavaScript error (browser console)
4. Old cache loaded

**Solution**:
1. **Check backend is running**:
   ```powershell
   curl http://127.0.0.1:8000/api/v1/health
   # Should return: {"status": "healthy"}
   ```

2. **Verify network connection**:
   - Ping: `ping google.com`
   - Check internet connection

3. **Check browser console**:
   - Press F12 → Console tab
   - Look for red error messages
   - Note exact error message

4. **Clear browser cache**:
   - Ctrl + Shift + Delete
   - Clear all browsing data
   - Close and reopen browser
   - Try again

5. **Try different browser**:
   - Use Chrome, Firefox, or Edge
   - See if issue persists

**Backend Check**:
```powershell
# Verify backend is responding
$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health"
Write-Host $response.Content
# Should show: {"status": "healthy"}
```

---

### Issue: "File Upload Fails - Error 500"

**Symptoms**:
- Click upload file
- Select PDF/Excel file
- Get error: "Server Error 500"
- File not uploaded

**Possible Causes**:
1. Backend server crashed
2. Out of disk space
3. File too large
4. Unsupported file type
5. Database connection lost

**Solution**:
1. **Check file size**:
   - Maximum: 50MB
   - If larger, compress first
   - Split large documents

2. **Check file type**:
   - Supported: PDF, Excel, CSV, Word
   - Not supported: images, videos
   - Convert if needed

3. **Check backend status**:
   ```powershell
   netstat -ano | findstr :8000
   # Should show running process
   ```

4. **Restart backend if needed**:
   ```powershell
   taskkill /IM python.exe /F
   Start-Sleep -Seconds 2
   # Restart backend service
   ```

5. **Check disk space**:
   ```powershell
   Get-Volume C: | Select-Object SizeRemaining
   # Should have at least 1GB free
   ```

6. **Check database connection**:
   - Login to Azure Portal
   - Check Cosmos DB status
   - Verify not throttled (429 errors)

---

### Issue: "Can't Download Export - Blank File"

**Symptoms**:
- Click Download
- File starts downloading
- File is empty or corrupted
- Can't open in Excel/PDF reader

**Possible Causes**:
1. Export process incomplete
2. Network interrupted during download
3. File type mismatch
4. Large file (> 2GB) browser limit

**Solution**:
1. **Wait for completion**:
   - Don't refresh or leave page during export
   - Wait for download notification
   - Check download folder

2. **Retry export**:
   - Go back to export
   - Click "Generate Export" again
   - Wait for completion
   - Download again

3. **Try different browser**:
   - Some browsers have file size limits
   - Try Chrome, Firefox, or Edge

4. **Check file type**:
   - Verify correct extension (.xlsx, .pdf)
   - Open with correct application
   - If still broken, retry export

---

## System Issues

### Issue: Backend Service Not Starting

**Symptoms**:
- Terminal shows error when starting backend
- Python command fails
- "Connection refused" on localhost:8000

**Error Messages**:
```
ModuleNotFoundError: No module named 'fastapi'
→ Solution: Run pip install -r requirements.txt

Port 8000 already in use
→ Solution: Kill existing process first

ConnectionError to Cosmos DB
→ Solution: Check environment variables
```

**Solution Steps**:

1. **Check Python is available**:
   ```powershell
   python --version
   # Should show: Python 3.x.x
   ```

2. **Activate virtual environment**:
   ```powershell
   cd backend
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt --quiet
   ```

4. **Kill existing process on port 8000**:
   ```powershell
   netstat -ano | findstr :8000
   # Find PID in last column
   taskkill /PID [PID] /F
   ```

5. **Set environment variables**:
   ```powershell
   $env:COSMOS_ENDPOINT="https://YOUR_ENDPOINT.documents.azure.com:443/"
   $env:COSMOS_KEY="YOUR_KEY"
   ```

6. **Start backend**:
   ```powershell
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

---

### Issue: "Cannot Connect to Database"

**Symptoms**:
- Backend starts but endpoints fail
- Error: "Could not connect to Cosmos DB"
- 503 Service Unavailable errors
- Timeouts on every request

**Diagnosis**:
```powershell
# Check if environment variables are set
echo $env:COSMOS_ENDPOINT
echo $env:COSMOS_KEY

# Test connection
python -c "
from services.cosmos_service import CosmosService
service = CosmosService()
print('Connection successful')
"
```

**Solution**:

1. **Verify credentials**:
   - Login to Azure Portal
   - Navigate to Cosmos DB
   - Copy endpoint URL correctly
   - Copy primary key (not secondary)

2. **Set environment variables correctly**:
   ```powershell
   # Endpoint should be:
   $env:COSMOS_ENDPOINT="https://myaccount.documents.azure.com:443/"
   
   # Key should be copied exactly
   $env:COSMOS_KEY="ABC123=="
   ```

3. **Check firewall rules**:
   - Azure Portal → Cosmos DB → Firewall
   - If IP filtering enabled, add your IP
   - Or allow all Azure services

4. **Check network connectivity**:
   ```powershell
   Test-NetConnection -ComputerName "YOUR_COSMOS.documents.azure.com" -Port 443
   # Should show ConnectionSucceeded: True
   ```

5. **Restart backend after fixes**:
   ```powershell
   taskkill /IM python.exe /F
   Start-Sleep -Seconds 2
   # Restart backend
   ```

---

### Issue: "Port 8000 Already in Use"

**Symptoms**:
- Error: "Address already in use"
- "Cannot bind to 127.0.0.1:8000"
- Another process using port

**Solution**:

1. **Find process using port**:
   ```powershell
   netstat -ano | findstr :8000
   # Shows: TCP 127.0.0.1:8000 [PID number]
   ```

2. **Kill the process**:
   ```powershell
   taskkill /PID [PID] /F
   # Or kill all Python processes
   taskkill /IM python.exe /F
   ```

3. **Verify port is free**:
   ```powershell
   netstat -ano | findstr :8000
   # Should show nothing
   ```

4. **Start backend again**:
   ```powershell
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

---

### Issue: "CORS Error - Cannot Call API"

**Symptoms**:
- Browser shows: "CORS policy blocked"
- API request shows 0 status code
- Network tab shows failed request
- Works in Postman, not in browser

**Solution**:

1. **Check if backend is running**:
   ```powershell
   curl http://127.0.0.1:8000/api/v1/health
   ```

2. **Verify frontend calling correct URL**:
   ```javascript
   // Check api.ts file
   // Should detect localhost and use: http://127.0.0.1:8000/api/v1
   
   // Or production: https://api.yourdomain.com/api/v1
   ```

3. **Check CORS configuration in main.py**:
   ```python
   # Should include frontend origin
   allow_origins = [
       "http://localhost:3000",
       "http://127.0.0.1:3000",
       "https://yourdomain.com"
   ]
   ```

4. **Restart both services**:
   ```powershell
   # Kill all processes
   taskkill /IM python.exe /F
   taskkill /IM node.exe /F
   
   # Restart backend
   # Restart frontend (npm run dev)
   ```

---

### Issue: "High Memory Usage"

**Symptoms**:
- Backend process taking 1+ GB RAM
- System slow
- Other applications struggling
- Backend crashes after hours

**Solution**:

1. **Check memory usage**:
   ```powershell
   Get-Process python | Select-Object ProcessName, @{
     Name="MemoryMB"; Expression={$_.WorkingSet/1MB}
   }
   ```

2. **If > 500MB**:
   - Likely memory leak
   - Restart backend

3. **Prevent future issues**:
   - Set up automatic restart (nightly)
   - Monitor memory trends
   - Look for memory leaks in code

---

### Issue: "Slow API Responses (> 2 seconds)"

**Symptoms**:
- API calls taking 2-5+ seconds
- Users report "slow loading"
- Dashboard hangs
- Export taking forever

**Diagnosis**:
```powershell
# Measure response time
$start = Get-Date
$response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/health"
$end = Get-Date
Write-Host "Response time: $(($end - $start).TotalMilliseconds)ms"
# Should be < 50ms for health check
```

**Solution**:

1. **Check database latency**:
   - Azure Portal → Cosmos DB → Metrics
   - Look at server-side latency
   - If > 100ms, increase RU/s

2. **Check CPU usage**:
   ```powershell
   Get-Counter -Counter "\Processor(_Total)\% Processor Time"
   # If > 80%, backend is overloaded
   ```

3. **Check network latency**:
   - If production, check Azure region
   - Consider multi-region failover

4. **Restart backend**:
   - Often resolves temporary slowness
   - Full restart clears caches

5. **Scale up resources**:
   - Increase RU/s for Cosmos DB
   - Move backend to larger VM
   - Consider load balancing

---

## Quick Troubleshooting Checklist

### "Something's Not Working"

1. [ ] Backend running? `netstat -ano | findstr :8000`
2. [ ] Database connected? `curl http://127.0.0.1:8000/api/v1/health`
3. [ ] Frontend running? Open `http://localhost:3000`
4. [ ] Check browser console: F12 → Console tab
5. [ ] Any red error messages? Try clearing cache
6. [ ] Backend logs showing errors? Check startup output
7. [ ] Recent code changes? Revert and retry
8. [ ] Environment variables set? `echo $env:COSMOS_ENDPOINT`
9. [ ] Port 8000 in use? Kill and restart
10. [ ] Still stuck? Check logs folder, enable debug logging

---

## Getting Help

### Information to Gather When Reporting Issues

1. **What were you doing?**
   - Step-by-step actions leading to issue

2. **What did you expect to happen?**
   - Normal/expected behavior

3. **What actually happened?**
   - Actual result/error

4. **Error messages**:
   - Exact text of any error
   - Screenshot of error if possible

5. **Environment**:
   - Browser type and version
   - Operating system
   - Network (home, office, VPN?)

6. **When did it start?**
   - After recent update?
   - Intermittent or always?
   - First time or recurring?

7. **Logs**:
   - Application Insights traces
   - Backend console output
   - Browser console errors

---

## Common Solutions

| Symptom | First Try | Second Try | Third Try |
|---------|-----------|-----------|-----------|
| Page blank | Refresh page | Clear cache | Restart browser |
| API fails | Check backend | Kill port 8000 | Restart backend |
| Can't login | Check email | Reset password | Check logs |
| File won't upload | Check size | Check type | Restart backend |
| Slow response | Wait 10s | Increase RU/s | Restart backend |
| Can't register | Clear form | Different email | Check console |

---

**Document Complete** - Last updated January 2026
