# ConnectifyU — Test Cases

| ID | Test | Result |
|---|---|---|
| TC-01 | Student login | PASS |
| TC-02 | Fresh student registrations | PASS |
| TC-03 | Browse events | PASS |
| TC-04 | Event details | PASS |
| TC-05 | Register | PASS |
| TC-06 | My registrations | PASS |
| TC-07 | Cancel own registration | PASS |
| TC-08 | Verify cancellation | PASS |
| TC-09 | Re-register after cancellation | DEFERRED / current backend rejects |
| TC-10 | Cancel another student's registration | PASS — rejected |
| TC-11 | Organizer sees own event registrations | PASS |
| TC-12 | Organizer accesses another organizer's registrations | PASS — rejected |
| TC-13 | Organizer dashboard shows own events | PASS |
| TC-14 | Organizer request | PASS |
| TC-15 | Admin pending requests | PASS |
| TC-16 | Admin approves request | PASS |
| TC-17 | Admin rejects request | PASS |
| TC-18 | Organizer creates event | PASS |
| TC-19 | Organizer cancels own event | PASS |
| TC-20 | Forgot password | PASS |
| TC-21 | Reset with valid token | PASS |
| TC-22 | Reuse reset token | PASS — rejected |
| TC-23 | Invalid/expired token | PASS — rejected |

## Frontend test account
Email: `connectifyu.frontend.test@gmail.com`  
Password: `Connectify@Test123`  
Role: student  
Roll no: `TEST003`

Never commit JWT tokens to GitHub.
