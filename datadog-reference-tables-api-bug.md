# Reference Tables API Pagination Bug Report

## Summary

The Reference Tables API (`GET /api/v2/reference-tables/tables`) has broken pagination that makes it impossible to retrieve more than 15 tables, regardless of the `limit` and `offset` query parameters used.

## Expected Behavior

1. The API should respect the `limit` query parameter to control page size
2. The API should respect the `offset` query parameter to skip items
3. The `meta.page.next_offset` should increment correctly to the next page
4. The `meta.page.next_offset` should be `null` when there are no more pages

## Actual Behavior

1. The API **ignores** the `limit` parameter and always returns exactly 15 items
2. The API **ignores** the `offset` parameter and always returns the same 15 items
3. The `meta.page.next_offset` is always `15` regardless of the current offset
4. The `meta.page.next_offset` never becomes `null`, even when paginating past the total number of tables

## Steps to Reproduce

Replace `YOUR_API_KEY` and `YOUR_APP_KEY` with valid credentials.

### Test 1: Limit parameter is completely ignored

```bash
# Request limit=1, but API returns 15 items
curl -s "https://api.datadoghq.com/api/v2/reference-tables/tables?limit=1" \
  -H "DD-API-KEY: YOUR_API_KEY" \
  -H "DD-APPLICATION-KEY: YOUR_APP_KEY" | jq '{items_returned: (.data | length)}'
```

**Result:** Returns 15 items even though `limit=1` was requested.

### Test 2: Offset parameter is ignored and next_offset is always the same

```bash
# Get first ID from offset=0
echo "offset=0:"
curl -s "https://api.datadoghq.com/api/v2/reference-tables/tables?limit=1&offset=0" \
  -H "DD-API-KEY: YOUR_API_KEY" \
  -H "DD-APPLICATION-KEY: YOUR_APP_KEY" | jq '{items_returned: (.data | length), first_id: .data[0].id, next_offset: .meta.page.next_offset}'

# Get first ID from offset=1 (should be different)
echo "offset=1:"
curl -s "https://api.datadoghq.com/api/v2/reference-tables/tables?limit=1&offset=1" \
  -H "DD-API-KEY: YOUR_API_KEY" \
  -H "DD-APPLICATION-KEY: YOUR_APP_KEY" | jq '{items_returned: (.data | length), first_id: .data[0].id, next_offset: .meta.page.next_offset}'

# Get first ID from offset=10 (should be different)
echo "offset=10:"
curl -s "https://api.datadoghq.com/api/v2/reference-tables/tables?limit=1&offset=10" \
  -H "DD-API-KEY: YOUR_API_KEY" \
  -H "DD-APPLICATION-KEY: YOUR_APP_KEY" | jq '{items_returned: (.data | length), first_id: .data[0].id, next_offset: .meta.page.next_offset}'
```

**Result:** All three requests return 15 items (not 1) with the **exact same first ID** and **next_offset is always 15**, proving both limit and offset are ignored and pagination metadata is broken.


## Impact

- **Cannot retrieve all reference tables** - Only the first 15 tables are accessible via the API
- **Infinite pagination loops** - Clients following `next_offset` will loop forever fetching the same 15 items
- **Breaking change** - If there are more than 15 reference tables in an organization, they cannot be programmatically accessed

## Environment

- API Endpoint: `https://api.datadoghq.com/api/v2/reference-tables/tables`
- API Version: v2 (latest)
- Tested Date: 2025-11-02
- Total reference tables in test org: 47 (per UI, but only 15 accessible via API)

## Workaround

None available. The API consistently returns only the same 15 tables regardless of pagination parameters.

## Expected Fix

1. Honor the `limit` query parameter up to a reasonable maximum (e.g., 1000)
2. Honor the `offset` query parameter to skip the specified number of items
3. Set `meta.page.next_offset` to `null` when there are no more pages
4. Correctly calculate `next_offset = current_offset + returned_items` for the next page

## Additional Notes

The API documentation at https://docs.datadoghq.com/api/latest/reference-tables/ indicates that `limit` and `offset` parameters should be supported for pagination, but they are not functioning as documented.
