# OpenAPI Schema Fix

## Problem

The OpenAPI schemas provided by Veeam Backup & Replication API contained a structural issue that prevented `openapi-python-client` from successfully generating a Python client. The error manifested as:

```
Unable to process schema /components/schemas/IBMCloudStorageBrowserSpec:

Cannot take allOf a non-object

Failure to process schema has resulted in the removal of:
/components/schemas/IBMCloudStorageBrowserSpec
```

## Root Cause

The issue occurred when parent schemas (like `CloudBrowserSpec`) were used as base schemas in `allOf` inheritance patterns but also contained `oneOf` and `discriminator` properties. This created an invalid schema structure:

**Problematic Pattern:**
```json
{
  "CloudBrowserSpec": {
    "type": "object",
    "properties": { ... },
    "oneOf": [
      { "$ref": "#/components/schemas/IBMCloudStorageBrowserSpec" },
      { "$ref": "#/components/schemas/AzureBlobBrowserSpec" },
      ...
    ],
    "discriminator": { ... }
  },
  "IBMCloudStorageBrowserSpec": {
    "allOf": [
      { "$ref": "#/components/schemas/CloudBrowserSpec" },
      { "type": "object", "properties": { ... } }
    ]
  }
}
```

This creates a circular dependency where:
1. The child schema (`IBMCloudStorageBrowserSpec`) extends the parent via `allOf`
2. The parent schema (`CloudBrowserSpec`) contains a `oneOf` that references the child
3. The `openapi-python-client` cannot resolve this circular structure

## Solution

The fix removes `oneOf` and `discriminator` from parent schemas that are referenced in `allOf` blocks. The corrected pattern:

**Fixed Pattern:**
```json
{
  "CloudBrowserSpec": {
    "type": "object",
    "properties": { ... }
  },
  "IBMCloudStorageBrowserSpec": {
    "allOf": [
      { "$ref": "#/components/schemas/CloudBrowserSpec" },
      { "type": "object", "properties": { ... } }
    ]
  }
}
```

Note: `oneOf` and `discriminator` have been removed from `CloudBrowserSpec`.

## Implementation

The `fix_openapi_schemas.py` script:
1. Scans all schemas to identify which ones are used as parents in `allOf` patterns
2. Removes `oneOf` and `discriminator` properties from those parent schemas
3. Preserves all other schema properties and relationships

## Schemas Fixed

The fix was applied to all three OpenAPI schema versions:

- **vbr_rest_1.2-rev1.json**: Fixed 41 schemas
- **vbr_rest_1.3-rev0.json**: Fixed 49 schemas
- **vbr_rest_1.3-rev1.json**: Fixed 55 schemas

Notable schemas that were fixed include:
- `CloudBrowserSpec`
- `CredentialsSpec` / `CredentialsModel`
- `JobSpec` / `JobModel`
- `RepositorySpec` / `RepositoryModel`
- `ProxySpec` / `ProxyModel`
- `TaskModel` / `TaskSessionModel`
- And many others...

## Verification

After applying the fix, `openapi-python-client generate` command completes successfully without any "Cannot take allOf a non-object" errors or schema removal warnings.

The remaining warnings about unsupported content types (e.g., `application/zip`, `application/x-tar`) are unrelated to the schema structure and are expected limitations of the client generator.

## Usage

To re-apply the fix to new OpenAPI schema files:

```bash
python3 fix_openapi_schemas.py
```

The script will automatically process all `.json` files in the `openapi_schemas/` directory.
