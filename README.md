# HomeReady Florida App (MVP)

This repository now contains a runnable HomeReady Florida MVP app with:

- Intake/profile creation
- Personalized plan generation
- Recurring reminder generation
- Revenue estimation
- Vendor recommendations

## Run the app

```bash
python -m homeready_florida.app
```

The server starts at `http://127.0.0.1:8080`.

## API quickstart

### 1) Create profile

```bash
curl -sS -X POST http://127.0.0.1:8080/api/profiles \
  -H 'Content-Type: application/json' \
  -d '{
    "full_name":"Alex Example",
    "email":"alex@example.com",
    "county":"Lee",
    "property_type":"single_family",
    "occupancy_status":"seasonal",
    "residents":2,
    "pets":1,
    "has_generator":true,
    "has_pool":true,
    "departure_month":"May",
    "return_month":"October"
  }'
```

### 2) Fetch full plan

```bash
curl -sS http://127.0.0.1:8080/api/profiles/<profile_id>/plan
```

### 3) Fetch reminders

```bash
curl -sS "http://127.0.0.1:8080/api/profiles/<profile_id>/reminders?months=3"
```

### 4) Estimate MRR

```bash
curl -sS -X POST http://127.0.0.1:8080/api/revenue/estimate \
  -H 'Content-Type: application/json' \
  -d '{"homeowners":180,"snowbirds":90,"managers":30,"vendor_sponsorship_mrr":750}'
```

### 5) Recommend vendors

```bash
curl -sS -X POST http://127.0.0.1:8080/api/vendors/recommend \
  -H 'Content-Type: application/json' \
  -d '{
    "county":"Lee",
    "needed_categories":["generator","pool"],
    "limit":3,
    "vendors":[
      {"name":"Best Storm","county":"Lee","categories":["generator","shutters"],"sponsored":true},
      {"name":"Alpha Pool","county":"Lee","categories":["pool"],"sponsored":false},
      {"name":"HVAC Pro","county":"Collier","categories":["hvac"],"sponsored":true}
    ]
  }'
```

## Tests

```bash
pytest
```
