# Authentication Test Scenarios

Complete test scenario documentation for auth.spec.ts

## Test Organization

```
Authentication Flow (50+ tests)
├── Login Page Display (3 tests)
│   ├── All required elements visible
│   ├── Proper input attributes
│   └── Branding and navigation
│
├── Successful Login (4 tests)
│   ├── Admin credentials
│   ├── Analyst credentials
│   ├── Viewer credentials
│   └── Token storage verification
│
├── Failed Login (4 tests)
│   ├── Invalid credentials
│   ├── Wrong password
│   ├── Non-existent user
│   └── Error clearing on retry
│
├── Form Validation (5 tests)
│   ├── Empty username validation
│   ├── Empty password validation
│   ├── Empty form submission
│   ├── Submit button states
│   └── Loading state handling
│
├── Logout (2 tests)
│   ├── Successful logout flow
│   └── Clear authentication data
│
├── Protected Routes (3 tests)
│   ├── Redirect unauthenticated users
│   ├── Allow authenticated access
│   └── Handle invalid tokens
│
├── Session Persistence (3 tests)
│   ├── Persist across page refresh
│   ├── Persist across navigation
│   └── Token restoration
│
├── Password Reset Flow (7 tests)
│   ├── Navigate to reset page
│   ├── Request reset with valid email
│   ├── Invalid email validation
│   ├── Reset with valid token
│   ├── Password mismatch validation
│   ├── Short password validation
│   └── Navigate back to login
│
├── Remember Me (2 tests)
│   ├── Checkbox visibility
│   └── Check/uncheck functionality
│
├── Security (3 tests)
│   ├── Password masking
│   ├── No credentials in URL
│   └── No token in console
│
└── Accessibility (3 tests)
    ├── Accessible form labels
    ├── Keyboard navigation
    └── Screen reader support
```

## Detailed Test Scenarios

### 1. Login Page Display

#### 1.1 All Required Elements Visible
**Given** User navigates to login page
**When** Page loads
**Then**
- Page title contains "Tiger ID"
- Username input is visible
- Password input is visible
- Submit button is visible
- Forgot password link is visible
- Form labels are visible

#### 1.2 Proper Input Attributes
**Given** User is on login page
**When** Inspecting form inputs
**Then**
- Username has name="username" and autocomplete="username"
- Password has type="password" and autocomplete="current-password"
- Submit button has type="submit"

#### 1.3 Branding and Navigation
**Given** User is on login page
**When** Page loads
**Then**
- "Tiger ID" heading is visible
- Tiger emoji/logo is displayed
- Version information is shown

---

### 2. Successful Login

#### 2.1 Admin Login
**Given** User is on login page
**When** User enters valid admin credentials
**And** Clicks submit
**Then**
- User is redirected to dashboard
- Header is visible
- Auth token is stored

#### 2.2 Analyst Login
**Given** User is on login page
**When** User enters valid analyst credentials
**And** Clicks submit
**Then**
- User is redirected to dashboard
- User can access analyst features

#### 2.3 Viewer Login
**Given** User is on login page
**When** User enters valid viewer credentials
**And** Clicks submit
**Then**
- User is redirected to dashboard
- User has viewer-level access

#### 2.4 Token Storage
**Given** User successfully logs in
**When** Login completes
**Then**
- Token is stored in localStorage
- Token has correct format (mock_token_*)

---

### 3. Failed Login

#### 3.1 Invalid Credentials
**Given** User is on login page
**When** User enters invalid username and password
**And** Clicks submit
**Then**
- Error message "Invalid username or password" is shown
- User remains on login page

#### 3.2 Wrong Password
**Given** User is on login page
**When** User enters valid username but wrong password
**And** Clicks submit
**Then**
- Error message is displayed
- User remains on login page

#### 3.3 Non-Existent User
**Given** User is on login page
**When** User enters username that doesn't exist
**And** Clicks submit
**Then**
- Error message is displayed
- No user information is exposed

#### 3.4 Error Clearing
**Given** User has failed login attempt with error shown
**When** User corrects credentials and submits
**Then**
- Previous error is cleared
- Login succeeds

---

### 4. Form Validation

#### 4.1 Empty Username
**Given** User is on login page
**When** User leaves username empty
**And** Enters password
**And** Clicks submit
**Then**
- Validation error "Username is required" is shown
- Form is not submitted

#### 4.2 Empty Password
**Given** User is on login page
**When** User enters username
**And** Leaves password empty
**And** Clicks submit
**Then**
- Validation error "Password is required" is shown
- Form is not submitted

#### 4.3 Empty Form
**Given** User is on login page
**When** User clicks submit without filling any fields
**Then**
- Both validation errors are shown OR form submission is prevented
- User remains on login page

#### 4.4 Submit Button States
**Given** User is filling login form
**When** User clicks submit
**Then**
- Button is disabled during submission
- Loading spinner is shown

---

### 5. Logout

#### 5.1 Logout Flow
**Given** User is authenticated and on any page
**When** User clicks user menu
**And** Clicks logout button
**Then**
- User is redirected to login page
- Auth token is cleared from localStorage

#### 5.2 Clear Auth Data
**Given** User is authenticated
**When** User logs out
**Then**
- Token is removed from localStorage
- User data is cleared
- Session cookies are cleared

---

### 6. Protected Routes

#### 6.1 Redirect Unauthenticated
**Given** User is not authenticated
**When** User tries to access protected route (/tigers, /facilities, etc.)
**Then**
- User is redirected to login page
- Original URL may be preserved for redirect after login

#### 6.2 Allow Authenticated Access
**Given** User is authenticated
**When** User navigates to protected routes
**Then**
- User can access all routes
- No redirects to login occur

#### 6.3 Invalid Token Handling
**Given** User has invalid/expired token
**When** User tries to access protected route
**Then**
- API request fails
- User is redirected to login
- Token is cleared

---

### 7. Session Persistence

#### 7.1 Page Refresh
**Given** User is authenticated and on /tigers page
**When** User refreshes the page
**Then**
- User remains authenticated
- User stays on /tigers page
- No redirect to login

#### 7.2 Navigation
**Given** User is authenticated
**When** User navigates between multiple protected routes
**Then**
- Authentication persists throughout
- No re-login required

#### 7.3 Token Restoration
**Given** User has valid token in localStorage
**When** User opens new browser tab/window
**And** Navigates to protected route
**Then**
- Token is read from localStorage
- User is authenticated automatically

---

### 8. Password Reset Flow

#### 8.1 Navigate to Reset Page
**Given** User is on login page
**When** User clicks "Forgot password?" link
**Then**
- User is redirected to /password-reset page

#### 8.2 Request Reset
**Given** User is on password reset page
**When** User enters valid email
**And** Clicks "Send Reset Link"
**Then**
- Success message is shown
- Message indicates email may be sent

#### 8.3 Invalid Email
**Given** User is on password reset page
**When** User enters invalid email format
**And** Clicks submit
**Then**
- Validation error "Please enter a valid email" is shown

#### 8.4 Reset with Token
**Given** User has password reset token
**When** User visits /password-reset?token=VALID_TOKEN
**And** Enters new password (8+ chars)
**And** Confirms password
**And** Clicks "Reset Password"
**Then**
- Success message is shown
- User is redirected to login after 3 seconds

#### 8.5 Password Mismatch
**Given** User is on password reset confirm page
**When** User enters different passwords in new/confirm fields
**And** Clicks submit
**Then**
- Validation error "Passwords don't match" is shown

#### 8.6 Short Password
**Given** User is on password reset confirm page
**When** User enters password less than 8 characters
**And** Clicks submit
**Then**
- Validation error "Password must be at least 8 characters" is shown

#### 8.7 Back to Login
**Given** User is on any password reset page
**When** User clicks "Back to Login" link
**Then**
- User is redirected to login page

---

### 9. Remember Me

#### 9.1 Checkbox Visibility
**Given** User is on login page
**When** Page loads
**Then**
- Remember me checkbox is visible
- Checkbox is unchecked by default

#### 9.2 Toggle Functionality
**Given** User is on login page
**When** User clicks remember me checkbox
**Then**
- Checkbox becomes checked
- Clicking again unchecks it

---

### 10. Security

#### 10.1 Password Masking
**Given** User is on login page
**When** User types in password field
**Then**
- Characters are masked (dots/asterisks)
- Input has type="password"

#### 10.2 No Credentials in URL
**Given** User logs in with credentials
**When** Login process completes
**Then**
- URL never contains username
- URL never contains password
- URL never contains auth token

#### 10.3 No Token in Console
**Given** User logs in successfully
**When** Checking browser console
**Then**
- Auth token is not logged
- Sensitive data is not exposed

---

### 11. Accessibility

#### 11.1 Form Labels
**Given** User is on login page
**When** Inspecting form
**Then**
- All inputs have associated labels
- Labels are properly linked (for/id)

#### 11.2 Keyboard Navigation
**Given** User is on login page
**When** User presses Tab key
**Then**
- Focus moves through: username → password → remember me → submit
- All interactive elements are reachable
- Focus is visible

#### 11.3 Screen Reader Support
**Given** User submits invalid form
**When** Validation errors appear
**Then**
- Errors are visible
- Errors have meaningful text
- Errors are associated with their inputs

---

## Test Data

### Valid Credentials
```javascript
admin:    { username: 'admin', password: 'admin123' }
analyst:  { username: 'analyst', password: 'analyst123' }
viewer:   { username: 'viewer', password: 'viewer123' }
```

### Invalid Credentials
```javascript
{ username: 'invaliduser', password: 'wrongpassword' }
{ username: 'admin', password: 'wrongpass' }
{ username: 'nonexistent', password: 'anypass' }
```

### Protected Routes
- `/dashboard`
- `/tigers`
- `/facilities`
- `/investigation2`
- `/templates`

## Success Criteria

All tests must:
1. ✅ Pass consistently (no flaky tests)
2. ✅ Complete within reasonable time (< 5 min total)
3. ✅ Clean up state after each test
4. ✅ Use proper assertions with meaningful messages
5. ✅ Follow Page Object Model pattern
6. ✅ Be independent and isolated
