# Version Roadmap

This document outlines the versioning strategy and planned releases for the Edgework project.

## Semantic Versioning

Edgework follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html): `MAJOR.MINOR.PATCH`

- **MAJOR** (0.x.x): Incompatible API changes or significant architectural changes
- **MINOR** (x.1.x): Backwards-compatible new features
- **PATCH** (x.x.1): Backwards-compatible bug fixes

### Version Bump Decision Tree

```
Is this change?
├─ Breaking API change → MAJOR version bump
├─ New feature → MINOR version bump
├─ Enhancement/Refactor → MINOR version bump
├─ Bug fix → PATCH version bump
└─ Documentation/Metadata → No version bump
```

## Current Status

- **Latest Release**: v0.5.0 (bug fixes)
- **Previous Release**: v0.4.9

> **Note**: v0.5.0 contains bug fixes that would typically be a PATCH release (v0.4.10). This version number is being retained as-is. Future releases will continue from v0.5.0.

## Planned Releases

### v0.5.1 - Upcoming Bug Fixes (PATCH)
**Status**: Pending
**Target**: As needed

**Potential Fixes**:
- Any reported bugs from v0.5.0
- Performance improvements
- Documentation corrections

### v0.6.0 - Player Enhancements (MINOR)
**Status**: Planned
**Target**: Q1 2025

**New Features**:
- Advanced player statistics filtering
- Player career stats endpoints
- Player comparison methods
- Enhanced player search with multiple criteria

**Changes**:
- Extend Player model with career data
- Add player stats aggregation methods
- Update player search API endpoints

### v0.7.0 - Team Features (MINOR)
**Status**: Planned
**Target**: Q1 2025

**New Features**:
- Team history endpoints
- Head-to-head team records
- Team performance analytics
- Extended roster management

**Changes**:
- Add Team history model
- Implement team comparison methods
- Enhanced roster data with player roles

### v1.0.0 - Stable Release (MAJOR)
**Status**: Planned
**Target**: Q2 2025

**Major Features**:
- Complete API coverage for all NHL endpoints
- Comprehensive caching layer
- Rate limiting and retry logic
- Full type hint coverage
- Stability guarantees

**Breaking Changes** (if any):
- Finalize public API surface
- Deprecated method removal
- Configuration changes

### v1.1.0 - Real-time Features (MINOR)
**Status**: Planned
**Target**: Q3 2025

**New Features**:
- WebSocket support for live game updates
- Real-time score tracking
- Live play-by-play data
- Streaming player statistics

### v1.2.0 - Advanced Analytics (MINOR)
**Status**: Planned
**Target**: Q4 2025

**New Features**:
- Advanced statistical calculations
- Predictive analytics endpoints
- Player performance trends
- Team strength metrics

### v2.0.0 - API Rewrite (MAJOR)
**Status**: Future
**Target**: 2026+

**Major Changes**:
- Asynchronous API client
- GraphQL API support (if NHL provides)
- Completely new architecture
- Potential breaking changes to client API

---

## Release Checklist

Before releasing any version:

### Pre-Release
- [ ] All tests pass (`pytest`)
- [ ] No new linting errors
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated with:
  - [ ] Version number
  - [ ] Release date
  - [ ] All changes categorized (Added/Fixed/Changed/Removed)
- [ ] New features documented
- [ ] Breaking changes documented

### Release Process
- [ ] Create release branch: `release/x.y.z`
- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md
- [ ] Commit changes
- [ ] Tag release: `git tag -a vx.y.z -m "Release v0.x.y.z"`
- [ ] Merge release to `main`
- [ ] Merge release to `develop`
- [ ] Push all branches and tags to origin

### Post-Release
- [ ] Create GitHub Release
- [ ] Update documentation if needed
- [ ] Publish to PyPI (for public releases)
- [ ] Announce changes

---

## Version History Notes

### Recent Releases Summary

| Version | Type | Date | Notes |
|---------|-------|------|-------|
| v0.5.0 | PATCH | 2025-02-01 | Bug fixes (schedule.games, Game._fetched flag) |
| v0.4.9 | MINOR | 2025-01-30 | Game model features |
| v0.4.8 | PATCH | 2025-01-28 | Schedule date filtering fixes |
| v0.4.7 | PATCH | 2025-01-28 | Schedule pagination fixes |
| v0.4.6 | PATCH | 2025-01-28 | Schedule pagination fixes |
| v0.4.5 | PATCH | 2025-01-28 | Schedule pagination fixes |
| v0.4.3 | PATCH | 2025-01-28 | Schedule pagination fixes |
| v0.3.1 | MINOR | 2025-06-24 | Documentation and enhancements |
| v0.2.1 | PATCH | 2025-06-19 | Player client fixes |
| v0.2.0 | MINOR | 2025-06-19 | Player list functionality |

### Known Issues

- **v0.4.4**: Missing (skipped in version sequence)
- **Date inconsistencies**: Some older releases have incorrect dates in CHANGELOG.md

---

## Decision Guidelines

### Current Version: v0.5.0

Based on current version, next versions would be:
- **PATCH fix** → v0.5.1
- **MINOR feature** → v0.6.0
- **MAJOR breaking change** → v1.0.0

### When to Use MAJOR Bumps

Use for:
- Removing or renaming public methods/classes
- Changing method signatures
- Changing return types of public APIs
- Major architectural rewrites
- API endpoint changes from NHL that break compatibility

Examples:
```python
# BEFORE
client.players(active_only=True)

# AFTER - BREAKING
client.get_players(include_inactive=False)
```

### When to Use MINOR Bumps

Use for:
- Adding new client methods
- Adding new model properties
- Adding optional parameters to existing methods
- New features that don't break existing code

Examples:
```python
# NEW FEATURE - MINOR BUMP
client.get_player_career_stats(player_id)

# NEW OPTIONAL PARAMETER - MINOR BUMP
client.players(active_only=True, season="2024-2025")
```

### When to Use PATCH Bumps

Use for:
- Bug fixes
- Performance improvements (no API changes)
- Documentation fixes
- Typo corrections
- Internal refactoring (no API changes)

Examples:
```python
# BUG FIX - PATCH BUMP
# Fixed: Schedule.games property returning empty list

# PERFORMANCE - PATCH BUMP
# Improved: API response caching reduces latency by 50%

# INTERNAL REFACTOR - PATCH BUMP
# Refactored: Internal HTTP client uses connection pooling
```

---

## Common Mistakes to Avoid

### ❌ Don't Bump MAJOR for Bug Fixes

**Wrong**:
```
v0.5.0 → v1.0.0 (for bug fix)
```

**Correct**:
```
v0.5.0 → v0.5.1 (for bug fix)
```

### ❌ Don't Bump MINOR for Bug Fixes

**Wrong**:
```
v0.5.0 → v0.6.0 (for bug fixes)
```

**Correct**:
```
v0.5.0 → v0.5.1 (for bug fixes)
```

> **Historical Note**: v0.5.0 contains bug fixes that would typically be a PATCH release. This was a deliberate decision to retain the version number. Future releases should follow semver strictly.

### ❌ Don't Skip Version Numbers

**Wrong**:
```
v0.5.0 → v0.7.0 (skipped v0.6.0)
```

**Correct**:
```
v0.5.0 → v0.6.0 → v0.7.0
```

### ❌ Don't Mix Unrelated Changes

**Wrong**: Releasing a feature and a bug fix together as a single release (unless they're closely related)

**Correct**: Separate releases:
- v0.6.0 for feature
- v0.5.1 for bug fix

### ❌ Don't Forget CHANGELOG

**Wrong**: Release without documenting changes

**Correct**: Always update CHANGELOG.md with:
- What was added/changed/fixed
- Why it was changed
- Any migration notes

---

## Version Compatibility Policy

### API Stability

- **0.x.x versions**: API may change between releases
- **1.0.0 and beyond**: Deprecation policy will apply
  - Deprecated methods will be supported for at least 2 minor versions
  - Breaking changes will be documented in migration guides

### Backwards Compatibility

- PATCH versions: Always backwards compatible
- MINOR versions: Always backwards compatible
- MAJOR versions: May contain breaking changes

---

## Feature Request Process

1. Submit issue on GitHub with feature request label
2. Discuss in issue comments
3. If accepted, add to appropriate version in roadmap
4. Implement on `develop` branch
5. Create feature branch from `develop`
6. Merge back to `develop` when ready
7. Release as part of next version

---

## Bug Fix Process

1. Report bug on GitHub
2. Reproduce and diagnose
3. Create `fix/*` branch from `main`
4. Fix bug
5. Add/verify tests
6. Create PR to `main`
7. Release as PATCH version

---

## Questions?

For questions about versioning or this roadmap, please:
- Open an issue on GitHub
- Check existing issues for similar discussions
- Review [Semantic Versioning](https://semver.org/spec/v2.0.0.html) documentation
