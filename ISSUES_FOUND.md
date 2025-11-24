# Issues Found in Images.py and Screenshots.py

This document describes issues discovered while adding test coverage for `bin/lib/objects/Images.py` and reviewing the related `bin/lib/objects/Screenshots.py` file.

## Issue 1: `get_description_models()` Missing Return Statement

**Files:** 
- `bin/lib/objects/Images.py` (line 94-99)
- `bin/lib/objects/Screenshots.py` (line 101-106)

**Problem:**
The `get_description_models()` method builds a list of description model names but never returns it. The method iterates through database fields, extracts model names from keys starting with `'desc:'`, and appends them to a `models` list, but the function ends without returning this list.

**Current Code:**
```python
def get_description_models(self):
    models = []
    for key in self._get_fields_keys():
        if key.startswith('desc:'):
            model = key[5:]
            models.append(model)
    # Missing: return models
```

**Expected Behavior:**
The method should return the list of description model names:
```python
def get_description_models(self):
    models = []
    for key in self._get_fields_keys():
        if key.startswith('desc:'):
            model = key[5:]
            models.append(model)
    return models  # Should return the list
```

**Impact:**
- Method currently returns `None` implicitly
- No callers found in codebase, so this may not currently break existing functionality
- If used in the future, it will fail silently

**Suggested Fix:**
Add `return models` at the end of the method.

---

## Issue 2: `get_meta()` Always Returns None for 'content' Field

**Files:**
- `bin/lib/objects/Images.py` (line 136-137)

**Problem:**
In `get_meta()`, when the `'content'` option is requested, it calls `get_content()` without arguments. The `get_content()` method defaults to `r_type='str'`, which returns `None`. As a result, requesting content in metadata always returns `None` instead of the actual file content.

**Current Code:**
```python
def get_meta(self, options=set(), flask_context=False):
    meta = self._get_meta(options=options, flask_context=flask_context)
    # ...
    if 'content' in options:
        meta['content'] = self.get_content()  # No args = r_type='str' = returns None
    # ...

def get_content(self, r_type='str'):
    if r_type == 'str':
        return None  # Always returns None when called without args
    else:
        return self.get_file_content()
```

**Expected Behavior:**
When `'content'` is requested in options, `get_meta()` should return the actual file content (BytesIO object), not `None`.

**Suggested Fixes:**

**Option A:** Call `get_content()` with appropriate parameter:
```python
if 'content' in options:
    meta['content'] = self.get_content(r_type='bytes')  # or 'file'
```

**Option B:** Change the default behavior of `get_content()` to return file content instead of None, but this might break other code.

**Impact:**
- API/UI requests for image content via `get_meta(options={'content'})` will always receive `None`
- This appears to be a bug that prevents content retrieval through the metadata API

---

## Issue 3: Incorrect Size Calculation in `create()` Functions

**Files:**
- `bin/lib/objects/Images.py` (line 171)
- `bin/lib/objects/Screenshots.py` (line 178, marked with `# FIXME STR SIZE LIMIT`)

**Problem:**
The size calculation uses `size = (len(content) * 3) / 4`, which is the formula for estimating decoded size from Base64-encoded text. However, in these functions:
1. When `b64=False` (default for Images.py), `content` is already binary bytes, so `len(content)` is the actual size
2. When `b64=True` (default for Screenshots.py), `content` is a base64-encoded string, but the size calculation happens BEFORE decoding (line 178 calculates, line 180-181 decodes), so it's using the wrong input
3. The formula `* 3 / 4` underestimates size, potentially allowing files larger than `size_limit` to be processed

**Current Code:**
```python
def create(content, size_limit=5000000, b64=False, force=False):
    size = (len(content)*3) / 4  # ❌ Wrong for binary, wrong for base64 timing
    if size <= size_limit or size_limit < 0 or force:
        if b64:
            content = base64.standard_b64decode(content.encode())  # Decoded AFTER size check
        # ...
```

**Expected Behavior:**
Size should be calculated correctly:
- If `b64=False`: `size = len(content)` (content is already binary)
- If `b64=True`: Calculate size of decoded content, or use `len(content) * 3 / 4` but verify timing

**Suggested Fix:**

**For Images.py (`b64=False` by default):**
```python
def create(content, size_limit=5000000, b64=False, force=False):
    if b64:
        # If base64, decode first, then check size
        content = base64.standard_b64decode(content.encode())
        size = len(content)
    else:
        # Content is already binary bytes
        size = len(content)
    
    if size <= size_limit or size_limit < 0 or force:
        image_id = sha256(content).hexdigest()
        # ...
```

**For Screenshots.py (`b64=True` by default):**
```python
def create_screenshot(content, size_limit=5000000, b64=True, force=False):
    if b64:
        # Decode first, then calculate actual size
        decoded_content = base64.standard_b64decode(content.encode())
        size = len(decoded_content)
        content = decoded_content
    else:
        # Content is already binary
        size = len(content)
    
    if size <= size_limit or size_limit < 0 or force:
        screenshot_id = sha256(content).hexdigest()
        # ...

---

## Summary

These issues were discovered while adding comprehensive test coverage for `Images.py`. All three issues appear to be bugs that could affect functionality:

1. **Issue 1**: Missing return statement (seems to be unused currently)
2. **Issue 2**: Content always returns None
3. **Issue 3**: Incorrect size calculation (known about already)

I'm happy to investigate these further and propose fixes if the maintainers would like.

---

## Testing Context

These issues were found while creating `tests/test_objects_images.py` which I will add in once we are happy Images.py is ok.

