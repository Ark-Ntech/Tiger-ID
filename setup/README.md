# Setup Files

All setup and launch scripts for Tiger ID.

## Directory Structure

```
setup/
├── windows/              # Windows batch files
│   ├── START_DOCKER.bat      # ⭐ Start everything with Docker
│   ├── STOP_DOCKER.bat       # Stop Docker services
│   ├── START_SERVERS.bat     # Start backend + frontend locally
│   ├── SETUP_ALL.bat         # Complete first-time setup
│   └── SETUP_DATABASE.bat    # Database setup only
├── scripts/              # Python setup scripts
│   ├── setup_all.py          # Complete system setup
│   ├── setup_database.py     # Database migrations + user creation
│   ├── create_test_user.py   # Create/update test user
│   ├── test_integration.py   # Integration tests
│   └── startup_check.py      # System validation
└── docs/                 # Setup documentation
    ├── SETUP_GUIDE.md        # Complete setup guide
    └── REACT_MIGRATION.md    # React migration details
```

## Quick Commands

### Start Everything (Docker)
```batch
setup\windows\START_DOCKER.bat
```

### Start Locally
```batch
setup\windows\START_SERVERS.bat
```

### First Time Setup
```batch
setup\windows\SETUP_ALL.bat
```

### Database Only
```batch
setup\windows\SETUP_DATABASE.bat
```

## Documentation

See `setup/docs/SETUP_GUIDE.md` for complete instructions.

## Scripts Usage

All Python scripts can be run directly:

```powershell
# Create test user
python setup\scripts\create_test_user.py

# Setup database
python setup\scripts\setup_database.py

# Test integration
python setup\scripts\test_integration.py

# Check system
python setup\scripts\startup_check.py
```

---

**For quickest start:** `setup\windows\START_DOCKER.bat`

