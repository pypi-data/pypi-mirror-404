# Changelog

## [0.5.0](https://github.com/typedef-ai/data-intelligence/compare/v0.4.1...v0.5.0) (2026-01-31)


### Features

* Add dbt test and unit test support to lineage graph ([#132](https://github.com/typedef-ai/data-intelligence/issues/132)) ([6f5513b](https://github.com/typedef-ai/data-intelligence/commit/6f5513bc713bfcae07f0b40ec11210c6583bf5ae))
* create implicit DEPENDS_ON edges, fix PhysicalRelation fqns ([#143](https://github.com/typedef-ai/data-intelligence/issues/143)) ([e47ad23](https://github.com/typedef-ai/data-intelligence/commit/e47ad230e34f04618bb57a6d96b6a27ddafffb1a))
* new demo reset devtool for tui workspace ([#134](https://github.com/typedef-ai/data-intelligence/issues/134)) ([c7fd10d](https://github.com/typedef-ai/data-intelligence/commit/c7fd10dcecce541970708f15cf548c355e376a4a))
* Physically Agnostic Incremental Loading  ([#121](https://github.com/typedef-ai/data-intelligence/issues/121)) ([39d16bb](https://github.com/typedef-ai/data-intelligence/commit/39d16bbf034796dc406c9b0035eae00deca36421))
* proper versioning in cli ([#146](https://github.com/typedef-ai/data-intelligence/issues/146)) ([5e7722b](https://github.com/typedef-ai/data-intelligence/commit/5e7722b5f85595d6446b21bc162cc2a409842c7c))


### Bug Fixes

* A few tweaks to benchmark and bedrock agents ([#141](https://github.com/typedef-ai/data-intelligence/issues/141)) ([6e38a03](https://github.com/typedef-ai/data-intelligence/commit/6e38a035b3e8614ab770fd576a5186fcb86f75ca))

## [0.4.1](https://github.com/typedef-ai/data-intelligence/compare/v0.4.0...v0.4.1) (2026-01-27)


### Bug Fixes

* support separate git configurations per project ([#133](https://github.com/typedef-ai/data-intelligence/issues/133)) ([44ac010](https://github.com/typedef-ai/data-intelligence/commit/44ac010c0a7df587f37b44155eae551d92791c26))

## [0.4.0](https://github.com/typedef-ai/data-intelligence/compare/v0.3.1...v0.4.0) (2026-01-27)


### Features

* add placeholder text for the agent screens ([0138828](https://github.com/typedef-ai/data-intelligence/commit/0138828873fb753811735d063b4f5e69fc90071c))
* add placeholder text for the agent screens ([#117](https://github.com/typedef-ai/data-intelligence/issues/117)) ([0138828](https://github.com/typedef-ai/data-intelligence/commit/0138828873fb753811735d063b4f5e69fc90071c))
* Benchmarks perform full and incremental graph builds ([#106](https://github.com/typedef-ai/data-intelligence/issues/106)) ([faa0c24](https://github.com/typedef-ai/data-intelligence/commit/faa0c24483c31bf2e90b463da64095e870337d2c))


### Bug Fixes

* handle new Linear API response format ([#127](https://github.com/typedef-ai/data-intelligence/issues/127)) ([37deb11](https://github.com/typedef-ai/data-intelligence/commit/37deb11059413434648d0d28e9060a0d9134c283))

## [0.3.1](https://github.com/typedef-ai/data-intelligence/compare/v0.3.0...v0.3.1) (2026-01-23)


### Bug Fixes

* local build regression from pypi README requirement ([#109](https://github.com/typedef-ai/data-intelligence/issues/109)) ([bb84348](https://github.com/typedef-ai/data-intelligence/commit/bb843486a3ae78bcdd499463474dcb839e3b1760))

## [0.3.0](https://github.com/typedef-ai/data-intelligence/compare/v0.2.0...v0.3.0) (2026-01-16)


### Features

* Deterministic-LLM Hybrid Analysis of dbt SQL ([#67](https://github.com/typedef-ai/data-intelligence/issues/67)) ([99e0dd6](https://github.com/typedef-ai/data-intelligence/commit/99e0dd6bf2398250385ccdb94405cb227c014e6b))


### Bug Fixes

* ensure that a uv venv exists in the project so we can run dbt cli. also moves profiles out of the project to limit project changes that need to be .gitignored ([#102](https://github.com/typedef-ai/data-intelligence/issues/102)) ([90da937](https://github.com/typedef-ai/data-intelligence/commit/90da937cc266a7394ef93219749fd96b76ccbdb9))
* regression in k8s builds caused by pypi doc req ([#104](https://github.com/typedef-ai/data-intelligence/issues/104)) ([d9b0719](https://github.com/typedef-ai/data-intelligence/commit/d9b0719b3072f4cb61a626cc63dd0ffe7ee723ae))

## [0.2.0](https://github.com/typedef-ai/data-intelligence/compare/v0.1.0...v0.2.0) (2026-01-13)


### Features

* Add Data Engineer tools/prompts to Pydantic CLI Agent, improved stability of logfire ([#32](https://github.com/typedef-ai/data-intelligence/issues/32)) ([08efbb1](https://github.com/typedef-ai/data-intelligence/commit/08efbb1fead1fd7727f641d42c85ec4086e8ca85))
* add rich progress tracking to ingest pipeline ([#47](https://github.com/typedef-ai/data-intelligence/issues/47)) ([91adc20](https://github.com/typedef-ai/data-intelligence/commit/91adc200a4d8f1e71756a31cf7024913545e973f))
* Add smart autoscroll control in TUI and enforce feature branch workflow for DE copilot ([#81](https://github.com/typedef-ai/data-intelligence/issues/81)) ([42e787d](https://github.com/typedef-ai/data-intelligence/commit/42e787db12d90585d9fc85559f4ebf464f76f385))
* Add support for bedrock models ([#58](https://github.com/typedef-ai/data-intelligence/issues/58)) ([7711bcc](https://github.com/typedef-ai/data-intelligence/commit/7711bcc37b33c13e940d275c171c07f63cdf6a62))
* add the daemon ticket based experience to the tui ([#70](https://github.com/typedef-ai/data-intelligence/issues/70)) ([fc87df8](https://github.com/typedef-ai/data-intelligence/commit/fc87df83100ad4f86189c6fc36d4dcb7f212169c))
* add TUI setup wizard with Textual (prototype) ([#49](https://github.com/typedef-ai/data-intelligence/issues/49)) ([6147e8c](https://github.com/typedef-ai/data-intelligence/commit/6147e8c5d5340144719d2e690f4b49a60065eb68))
* adding a webui for data analyst ([#2](https://github.com/typedef-ai/data-intelligence/issues/2)) ([9096a18](https://github.com/typedef-ai/data-intelligence/commit/9096a186c56087c101ec46c1a82ccebd90103593))
* dev docker compose ([#4](https://github.com/typedef-ai/data-intelligence/issues/4)) ([97e1d73](https://github.com/typedef-ai/data-intelligence/commit/97e1d73aa6de637eebe5f245e41ad71ad597ba97))
* falkordb full text search, snowflake db visibility filtering ([#46](https://github.com/typedef-ai/data-intelligence/issues/46)) ([5110928](https://github.com/typedef-ai/data-intelligence/commit/5110928ae576303fbe25456ae718e93d136213f5))
* full clustering implementation ([#10](https://github.com/typedef-ai/data-intelligence/issues/10)) ([71bebad](https://github.com/typedef-ai/data-intelligence/commit/71bebad07d0060dc0a07224472bffd0c0db4db88))
* Improve demo workflow with benchmark branch preservation and session management cleanup ([#64](https://github.com/typedef-ai/data-intelligence/issues/64)) ([df015f8](https://github.com/typedef-ai/data-intelligence/commit/df015f8613d532a14b7eada0b7c7c05c7719edf9))
* Mattermost clones working plus tasks for scenarios ([#43](https://github.com/typedef-ai/data-intelligence/issues/43)) ([fd77b49](https://github.com/typedef-ai/data-intelligence/commit/fd77b49b4ebd5f2905f9c227c0479a20f5c09d98))
* prototype benchmark for data-intelligence ([#26](https://github.com/typedef-ai/data-intelligence/issues/26)) ([de2871a](https://github.com/typedef-ai/data-intelligence/commit/de2871afdd78d586fbcd3da86d82d9bf1522d616))
* separate logical and physical concepts ([#20](https://github.com/typedef-ai/data-intelligence/issues/20)) ([3a9bd05](https://github.com/typedef-ai/data-intelligence/commit/3a9bd05cd6b07328d5098893574a1ab7477a17ef))


### Bug Fixes

* **backend/docker:** misc path/entrypoint fixes to get it running ([#22](https://github.com/typedef-ai/data-intelligence/issues/22)) ([aa47c3f](https://github.com/typedef-ai/data-intelligence/commit/aa47c3fba30895bde9f107d3f9bea4014fb2a8b1))
* daemon only grabs labeled tickets ([#18](https://github.com/typedef-ai/data-intelligence/issues/18)) ([748f6c3](https://github.com/typedef-ai/data-intelligence/commit/748f6c332cb5fac490f4c6645a2bdab7d4749e07))
* if the dbt project gets cloned with git, enable git in the config ([#73](https://github.com/typedef-ai/data-intelligence/issues/73)) ([6e99162](https://github.com/typedef-ai/data-intelligence/commit/6e9916232ab569c4385cbf54d6651c1312517c92))
* limit the daemon to only process tickets assigned to data-engineer-agent ([#74](https://github.com/typedef-ai/data-intelligence/issues/74)) ([ac94267](https://github.com/typedef-ai/data-intelligence/commit/ac94267c4965b040977cdf3933f39ace67cd06e1))
* minor fixes to get medallion + frontend to work ([#59](https://github.com/typedef-ai/data-intelligence/issues/59)) ([1444285](https://github.com/typedef-ai/data-intelligence/commit/1444285ba030a4a2f242a4494e102f106d81d868))
* readme ([#1](https://github.com/typedef-ai/data-intelligence/issues/1)) ([172767a](https://github.com/typedef-ai/data-intelligence/commit/172767a78d33c963e5a09685b34f5016bd7a9714))
