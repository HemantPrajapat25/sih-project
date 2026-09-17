# Privacy-By-Design Guarantee

## Regulatory & Ethical Principles

NumberGuard strictly implements privacy-by-design to eliminate the risk of subscriber identity leakage during mobile number recycling.

### 1. Absolute Prohibition of Personal Data
The platform **never** accepts, processes, stores, or transmits:
- Subscriber full names
- Physical or residential addresses
- Government ID documents (Aadhaar, PAN, Passport)
- Account passwords, PINs, or credentials
- Call records, SMS contents, or OTP histories
- Financial balances or transaction histories

### 2. Cryptographic Masking & One-Way HMAC Indexing
- **In UI & Public APIs**: Phone numbers are strictly formatted as masked strings preserving only country code and the last 3 digits: `+91 98**** *210`.
- **Database Indexing**: The backend uses an HMAC-SHA256 hash computed with a secret server-side pepper key (`PHONE_HASH_PEPPER`). Even if the database were compromised, the original phone numbers cannot be recovered via dictionary attacks.
- **Provider Challenge References**: When alerting banks or digital platforms, the notification payload references an opaque, non-reversible surrogate token: `REF-A3E89B1F20C1`.

### 3. No Private Web Scraping
NumberGuard does **not** scrape banking websites, search engines, or private portals. Integrations are strictly opt-in, authenticated B2B webhooks provided by participating digital service providers.
