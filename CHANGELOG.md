# CHANGELOG

<!-- version list -->

## v1.2.1 (2026-06-05)

### Bug Fixes

- **stream**: Check active status and recreate inactive sounddevice streams
  ([`4f0aa91`](https://github.com/tothKarolyDavid/bt-keepalive/commit/4f0aa913edaaa2795a900884dbb80cc9af0ca493))

### Continuous Integration

- Configure python-semantic-release and add to dev dependencies
  ([`5d6eea6`](https://github.com/tothKarolyDavid/bt-keepalive/commit/5d6eea658ae5a4194e125d91fd9bcb5b8b93cff2))

- Update GitHub Actions dependency versions
  ([`96c6df1`](https://github.com/tothKarolyDavid/bt-keepalive/commit/96c6df1857206e7ad10ad23308ee1d2314d31f4f))

- Update release workflow to automate release process on push to main
  ([`21072ef`](https://github.com/tothKarolyDavid/bt-keepalive/commit/21072ef82cf72b71d70b8d96b76a9b6157ca868e))

### Testing

- **stream**: Add test for stream active state and auto-recreation
  ([`514babe`](https://github.com/tothKarolyDavid/bt-keepalive/commit/514babe55505d1a3d53584b9d047e9f6230040f8))

- **stream**: Fix lint errors in test_stream_state.py
  ([`66e8417`](https://github.com/tothKarolyDavid/bt-keepalive/commit/66e8417905498f18127a5f31b215ddbcd70b5e7a))


## v1.2.0 (2026-06-04)

### Build System

- Disable UPX compression in PyInstaller spec
  ([`bc5ae9e`](https://github.com/tothKarolyDavid/bt-keepalive/commit/bc5ae9e2c9e5db4444843a6c198b55a1417e73cd))

### Chores

- Consolidate dev install and expand gitignore
  ([`394c4f6`](https://github.com/tothKarolyDavid/bt-keepalive/commit/394c4f6ebcf9b44ea54568a129cc351ebaaa3222))

- **release**: Bump version to 1.2.0
  ([`2f5f979`](https://github.com/tothKarolyDavid/bt-keepalive/commit/2f5f979066183daef0e3e8fc2af2c7ce1b96d969))

### Code Style

- Normalize punctuation in UI strings and comments
  ([`d6cb30c`](https://github.com/tothKarolyDavid/bt-keepalive/commit/d6cb30cc7a693e7e02a65d6414c005bf69b39319))

### Continuous Integration

- Add quality gates to release workflow and dependabot
  ([`4ab2f98`](https://github.com/tothKarolyDavid/bt-keepalive/commit/4ab2f98d087accaad2803e26fe9dc6781c0c1161))

- Install editable package in workflow
  ([`eded7af`](https://github.com/tothKarolyDavid/bt-keepalive/commit/eded7af1bcf540460f07e3fcb45bd16715a0c969))

### Documentation

- Normalize punctuation in README and release notes
  ([`1bced23`](https://github.com/tothKarolyDavid/bt-keepalive/commit/1bced233b20f110ef3da10b38b7c75861ee760d3))

- Simplify tray menu and config documentation
  ([`45a2ffd`](https://github.com/tothKarolyDavid/bt-keepalive/commit/45a2ffd03b3fc986b977c8775234fcd4385e859c))

### Features

- **version**: Read package version from pyproject.toml
  ([`6d0988a`](https://github.com/tothKarolyDavid/bt-keepalive/commit/6d0988a155b55b966f06a9c23d13fd5a708f2d08))

### Refactoring

- Remove silent preset and pulse interval dialog
  ([`3eae01c`](https://github.com/tothKarolyDavid/bt-keepalive/commit/3eae01cc8cd6ac14428d4b09bc8e14fcf6bdb2f0))

- **stream**: Extract blocksize helper and expand pulse tests
  ([`3683074`](https://github.com/tothKarolyDavid/bt-keepalive/commit/3683074ea3ad5debc3be59ccfd5d952ce886e833))

### Testing

- Add app, binaural, startup, and single-instance coverage
  ([`2478a5c`](https://github.com/tothKarolyDavid/bt-keepalive/commit/2478a5c5f9e5ecb17c1ffd04bfe6c88e0ab0918f))


## v1.1.0 (2026-06-04)

- Initial Release
