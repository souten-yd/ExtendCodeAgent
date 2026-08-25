# External AI Audit Request — Context Virtualization / Semantic Working Set

以下は、別AIへそのまま渡せる独立監査依頼文です。

---

## 依頼文

あなたは `souten-yd/ExtendCodeAgent` の**独立アーキテクチャ監査役**として振る舞ってください。

監査対象は、Context Virtualization / Semantic Working Set によって、大規模Projectでも
primary coding modelの1回あたりの総Contextを最大64k、目標p95 32k程度へ抑えつつ、品質を
維持または改善する設計です。

### 対象Repository / Branch

- Repository: `souten-yd/ExtendCodeAgent`
- Review branch: `agent/context-virtualization-semantic-working-set`
- Base reviewed when the proposal was created:
  `7bab478709d125722e57fd99dd95b784e0ce62c7`

レビュー開始時には必ず最新のbranch/baseを取得し、上記SHAを無条件に最新と仮定しないで
ください。

### 最初に読む文書

1. `AGENTS.md`
2. `docs/PI_MASTER_EXECUTION_PLAN.md`
3. `docs/handoff/NEXT_TASK.md`
4. `docs/handoff/C2_EVIDENCE_DELIVERY_DECISION.md`
5. `docs/handoff/C2_CONTEXT_VIRTUALIZATION_AND_SEMANTIC_WORKING_SET_DESIGN.md`
6. `docs/audit/CONTEXT_VIRTUALIZATION_ARCHITECTURE_AUDIT.md`
7. `docs/evaluation/large-project-bounded-context-target-v1.json`
8. `docs/evidence/final/baseline-gap-report.md`

ただし、**文書に書いてあることを実装済み事実として扱わないでください。**
必ずproduction code、tests、evidenceと照合してください。

### 監査の最重要目的

この設計が本当に以下を実現できるか、批判的に判定してください。

> Repository全体をLLM Contextへ保持するのではなく、revision-awareなProject Truth / Twin /
> Verification / Task state等をECA側へ保持し、TaskごとのSemantic Working Setだけをモデルへ
>渡すことで、大規模Projectでも高品質なローカルLLMを長大Contextなしで利用する。

Context削減そのものを目的化しないでください。品質・critical evidence・Verification・
truthfulnessを維持できない32kは失敗です。

### 必須監査観点

#### 1. 現行コードを実際に確認する

最低限、以下を確認してください。

```text
src/extendcodeagent/core/
src/extendcodeagent/graph/
src/extendcodeagent/twin/
src/extendcodeagent/analysis/
src/extendcodeagent/context/
src/extendcodeagent/orchestration/
src/extendcodeagent/verification/
src/extendcodeagent/runtime/
src/extendcodeagent/testing/
src/extendcodeagent/traceability/
src/extendcodeagent/blueprint/
src/extendcodeagent/convergence/
src/extendcodeagent/storage/
src/extendcodeagent/service/application.py
adapters/opencode/
```

特に、既存の以下を再利用できるか確認してください。

- `GraphNode` / `GraphEdge` / `GraphEvidence`
- `TwinService`
- `SemanticChangeSet`
- `VerificationObligation` / `RequiredVerificationSet`
- `TaskSignals` / `TaskIntent` / `IntelligencePlan`
- runtime observations
- Traceability
- Blueprint / Convergence
- shared SQLite owner

#### 2. 重複実装を厳しく探す

提案されている各概念について、既存コードを先に探し、以下のどれかに分類してください。

```text
REUSE
EXTEND
PROJECT
CONSOLIDATE
NEW
```

対象：

```text
EvidenceAtom
Semantic Contract
Semantic ABI / contract fingerprint
Semantic Working Set
Evidence Gap
ChangeCapsule
Context Compiler
TaskExecutionState
Task DAG
Project/Evolution Memory
Context Debt
```

既存型・serviceを少し改修すれば済むのに新しい並行systemを作る提案は、明確に批判して
ください。

次のような二重所有は原則NGです。

```text
ContractStore separate from Graph/Twin
RuntimeMemoryStore separate from RuntimeObservation
RequirementGraph separate from Traceability/Graph
TaskPlannerV2 separate from Orchestration/Blueprint/Convergence
VerificationObligationV2 separate from verification contracts
second SQLite/database for context/memory
LLM-generated project summary treated as Project Truth
```

#### 3. 長Contextが必要だった本当の原因を再分析する

次の要因を分離してください。

- source/tool探索量
- PI serialization bloat
- conversation/task-state保持
- requirement/design intent保持
- API/interface/side-effect不明
- UI/API/backend cross-boundary不明
- exact schema/output copying error
- verification scope discovery
- model reasoning capability自体の不足
- provider/runtime protocol overhead
- cached/prefix context
- output/reasoning tokens

「Context Compilerを作れば全部解決する」とは仮定しないでください。

#### 4. Semantic Contract / ABIを厳しく評価する

特に以下を確認してください。

- Python/JS/TSの既存parser/analyzerから二重parseなしで抽出できるか
- 入力/出力/type/export/API/effect/stateなど、何を確実に抽出できるか
- unknownをどう保持するか
- contract fingerprintでImpact伝播を止めた際のfalse negative
- modeled contract不変とruntime behavior不変を混同していないか
- side effectをどのconfidence/statusで扱うべきか
- contract専用nodeを作る必要が本当にあるか

危険ならSemantic ABIを却下またはshadow限定にしてください。

#### 5. Twin / invalidation / Memoryを監査する

新しいcache/memory/task-stateには必ず、

```text
project/workspace
Twin/source revision
producer/analyzer version
provenance
freshness
dependency closure
invalidation reason
```

の対応があるか確認してください。

MemoryによるContext削減より、stale truth再利用の方が危険です。

Generic chat memory / free-text vector memoryをProject Truthとして扱う案は拒否してください。

#### 6. Task管理が本当に必要か確認する

新Task engineを作る前に、

- C1 Orchestration
- Blueprint
- Convergence
- Verification Obligations
- Evidence IDs / trace

で何が表現できるか確認してください。

`TaskExecutionState`やTask DAGが必要なら、足りない状態だけを最小contractとして提案して
ください。

#### 7. Context Compilerの責任分離を監査する

以下を一つの巨大classにしないでください。

```text
candidate projection
EvidenceAtom projection
protected evidence selection
coverage optimizer
sufficiency checker
targeted expansion
working set envelope
AnswerIR / ChangeIR
serialization
```

各責務が既存domainのどこに属すべきか提案してください。

#### 8. メンテナンス性とRefactoringを評価する

特に：

- `src/extendcodeagent/service/application.py`
- `src/extendcodeagent/orchestration/service.py`
- `src/extendcodeagent/context/service.py`
- Python/JS/TS analyzers
- storage
- `tools/local/evaluation_runner.py`

を確認してください。

Refactorは以下に分類してください。

```text
REQUIRED_BEFORE_FEATURE
DO_WITH_FEATURE
SAFE_LATER
NOT_WORTH_IT
```

単に行数が多いという理由だけでframework化や全面rewriteを提案しないでください。

#### 9. 32k / 64kの成立性を検証する

次のCompression Curveを評価計画へ含めてください。

```text
8k
16k
24k
32k
48k
64k
```

必ずprimary-modelの**総Context**を評価してください。

inputだけ64k未満でもoutput headroomを含めて65,536を超えるなら、64k profile PASSでは
ありません。

Task classごとに、

```text
16K_CAPABLE
32K_CAPABLE
64K_CAPABLE
NEEDS_DECOMPOSITION
NOT_YET_SUPPORTED
```

のどれが妥当か判断してください。

#### 10. 量子化改善との因果を混同しない

ECAの狙いは、長Context/KV用メモリを削減し、より低い量子化度合い・より高品質なlocal
modelへ資源を回しやすくすることです。

ただしECAがquantization/model loading/schedulerを所有する必要はありません。

Context削減とQ4→Q6/Q8等の品質改善を同時に変えて「ECAで精度が上がった」と結論しないで
ください。Controlled comparisonを要求してください。

#### 11. Security / Trust

Repository内文字列はuntrusted dataです。

- repo textがcontrol instructionへ昇格しないこと
- LLM summaryがProject Truthにならないこと
- memoryがrollout/privacy/depthを変更しないこと
- evidence ID pagingでworkspace越境しないこと
- external researchがverified project factにならないこと

を確認してください。

### 必ず否定的観点も出すこと

監査結果には最低限、以下を含めてください。

1. この設計で最も誤っている可能性が高い仮定5個
2. Over-engineeringになりそうな箇所5個
3. 削除・統合・延期すべきmechanism
4. 既存ECAコードだけで既に解決できている提案
5. 32kで破綻しそうなTask class
6. Greenfieldで破綻しそうな箇所
7. UI/browser/API/backend変更で破綻しそうな箇所
8. stale memory / invalidationのfailure mode
9. 実装後にmaintenance hotspotになりそうな箇所
10. 提案の80%の価値をもっと小さいarchitectureで得る代替案

### 出力形式

以下の順で回答してください。

#### A. Executive verdict

```text
ADOPT_AS_DESIGNED
ADOPT_WITH_CHANGES
NARROW_AND_RETEST
REJECT
```

から1つ。

#### B. Current implementation verification

各主張について：

```text
CONFIRMED / PARTIAL / FALSE / STALE
exact file/type/function
evidence/rationale
```

#### C. Severity-ranked findings

```text
BLOCKER / HIGH / MEDIUM / LOW
```

#### D. Duplication / consolidation table

各新概念を：

```text
REUSE / EXTEND / PROJECT / CONSOLIDATE / NEW
```

に分類。

#### E. Refactoring verdict

各Refactorを：

```text
REQUIRED_BEFORE_FEATURE
DO_WITH_FEATURE
SAFE_LATER
NOT_WORTH_IT
```

に分類。

#### F. 32k / 64k feasibility

Task class別に上限と不足proofを提示。

#### G. Revised architecture

より小さく安全な構成があれば、提案設計より優先して提示。

#### H. Missing tests/evidence

active adoption前に追加すべきtest/evidenceを具体化。

#### I. Go / No-Go

次にmergeを許可すべき**最小実装slice**を1つだけ提示。

### 最終ルール

この監査の目的は設計を褒めることではありません。

**不要な機能を削り、既存資産を最大限再利用し、32k/64kという目標を品質非劣化の範囲で
最小のarchitectureによって達成できるかを判定すること**です。

コード変更は依頼しません。まず監査結果だけを返してください。
