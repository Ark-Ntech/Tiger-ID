# Setup Scripts

Python scripts for system setup and validation.

## Scripts

### setup_all.py
Complete system setup - installs all dependencies and configures database.

```powershell
python setup\scripts\setup_all.py
```

### setup_database.py
Database setup - runs migrations and creates test user.

```powershell
python setup\scripts\setup_database.py
```

### create_test_user.py
Create or update test user.

```powershell
# Default (admin/admin)
python setup\scripts\create_test_user.py

# Custom user
python setup\scripts\create_test_user.py --username myuser --password mypass
```

### test_integration.py
Test frontend-backend communication.

```powershell
python setup\scripts\test_integration.py
```

### startup_check.py
Validate system requirements and configuration.

```powershell
python setup\scripts\startup_check.py
```

---

## When to Use Each Script

**First time setup:**
```powershell
python setup\scripts\setup_all.py
```

**Database issues:**
```powershell
python setup\scripts\setup_database.py
```

**Login problems:**
```powershell
python setup\scripts\create_test_user.py
```

**Verify everything works:**
```powershell
python setup\scripts\test_integration.py
```

**Check system health:**
```powershell
python setup\scripts\startup_check.py
```

---

**Prefer batch files?** See `setup/windows/README.md`

