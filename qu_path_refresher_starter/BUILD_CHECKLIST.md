# Build Checklist

## API and cache
- [ ] Environment variables load
- [ ] Authentication returns a token
- [ ] First menu request returns 200
- [ ] X-Generation-Time is saved
- [ ] Full menu is cached
- [ ] Second request sends PrevGenerationTime
- [ ] Empty/204 response reuses cache
- [ ] Cache is separated by context

## Parser
- [ ] Nested children are flattened
- [ ] PLU is read safely
- [ ] Ancestors are retained
- [ ] Multiple paths per item ID are retained

## Workbook and matching
- [ ] PLUs remain strings
- [ ] QU Item ID is primary key
- [ ] PLU confirms identity
- [ ] Ambiguous paths require review

## Outputs
- [ ] CSV report is generated
- [ ] UPDATED paths are clear
- [ ] Unsafe matches are excluded
- [ ] Original simulator JSON is not overwritten
