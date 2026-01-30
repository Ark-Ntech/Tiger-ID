# Start Tiger ID Application on alternate ports
# Frontend: 5174, Backend: 8001

Write-Host "Starting Tiger ID Application..."
Write-Host "Frontend: http://localhost:5174"
Write-Host "Backend: http://localhost:8001"
Write-Host ""

# Start backend on port 8001
Write-Host "Starting backend on port 8001..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python -m uvicorn backend.api.app:app --host 0.0.0.0 --port 8001 --reload"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start frontend on port 5174
Write-Host "Starting frontend on port 5174..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm run dev"

Write-Host ""
Write-Host "Tiger ID Application Started!"
Write-Host "Frontend: http://localhost:5174"
Write-Host "Backend: http://localhost:8001"
Write-Host "Backend API Docs: http://localhost:8001/docs"
Write-Host ""
Write-Host "Press Ctrl+C in each terminal window to stop the services"

