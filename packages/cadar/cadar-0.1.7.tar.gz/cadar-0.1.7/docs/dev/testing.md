# Testing

CaDaR has comprehensive test coverage to ensure reliability and correctness.

## Test Organization

Tests are organized by module:

- **Unit tests** - In `src/` alongside source code
- **Integration tests** - In `src/lib.rs`
- **Python tests** - In `tests/` directory (if any)

## Running Tests

### All Tests

Run all Rust tests:

```bash
cargo test
```

Expected output:
```
running 41 tests
test result: ok. 41 passed; 0 failed; 0 ignored
```

### Specific Module Tests

Test a specific module:

```bash
# Test script detection
cargo test script_detection

# Test normalization
cargo test normalization

# Test ICR
cargo test icr
```

### Verbose Output

See detailed test output:

```bash
cargo test -- --nocapture
```

### Single Test

Run a specific test:

```bash
cargo test test_ara2bizi -- --nocapture
```

## Test Coverage

Current test coverage by module:

- ✅ Script Detection (4 tests)
- ✅ Normalization (5 tests)
- ✅ Tokenization (4 tests)
- ✅ ICR Generation (4 tests)
- ✅ Script Generation (3 tests)
- ✅ Validation (6 tests)
- ✅ Integration (6 tests)
- ✅ Types (4 tests)
- ✅ Dialect (3 tests)

**Total: 41 tests**

## Writing Tests

### Unit Test Example

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arabic_to_latin() {
        let processor = CaDaR::new(Dialect::Moroccan);
        let result = processor.ara2bizi("سلام").unwrap();
        assert_eq!(result, "slam");
    }
}
```

### Integration Test Example

```rust
#[test]
fn test_round_trip() {
    let processor = CaDaR::new(Dialect::Moroccan);

    let original = "سلام عليكم";
    let latin = processor.ara2bizi(original).unwrap();
    let back = processor.bizi2ara(&latin).unwrap();

    // Compare standardized forms
    let orig_std = processor.ara2ara(original).unwrap();
    let back_std = processor.ara2ara(&back).unwrap();

    assert_eq!(orig_std, back_std);
}
```

## Test Data

Common test phrases:

```rust
// Greetings
"سلام" → "slam"
"السلام عليكم" → "salam 3likom"

// Questions
"كيفاش داير؟" → "kifash dayer?"
"واش بخير؟" → "wash bkhir?"

// Common words
"واخا" → "wakha"
"بزاف" → "bzaf"
"شوية" → "shwiya"
```

## Python Testing

Test Python bindings:

```bash
python -c "
import cadar

# Test basic functionality
assert cadar.ara2bizi('سلام', darija='Ma') == 'slam'
assert cadar.bizi2ara('slam', darija='Ma') == 'سلام'

print('✓ All Python tests passed')
"
```

## Continuous Integration

Tests run automatically on GitHub Actions for:

- Every push to main branch
- Every pull request
- All tagged releases

See `.github/workflows/` for CI configuration.

## Performance Testing

While not automated, you can benchmark:

```bash
# Run benchmarks (requires criterion)
cargo bench
```

## Testing Guidelines

When adding new features:

1. **Write tests first** (TDD approach)
2. **Test edge cases**:
   - Empty input
   - Very long input
   - Mixed scripts
   - Special characters
3. **Test error conditions**
4. **Maintain test coverage**

## Debugging Tests

Run tests with debug output:

```bash
RUST_LOG=debug cargo test -- --nocapture
```

Use `dbg!` macro in tests:

```rust
#[test]
fn test_something() {
    let result = some_function();
    dbg!(&result);  // Print debug info
    assert_eq!(result, expected);
}
```

## Test Failures

If tests fail:

1. Read the error message carefully
2. Run the specific failing test in verbose mode
3. Check recent changes to the code
4. Verify test data and expectations
5. Consider edge cases

## Coverage Reports

Generate coverage reports (requires tarpaulin):

```bash
cargo install cargo-tarpaulin
cargo tarpaulin --out Html
```

View report in `tarpaulin-report.html`.

For more information, see [Building from Source](building.md) and [Contributing](contributing.md).
