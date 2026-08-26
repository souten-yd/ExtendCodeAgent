# 第三者AI監査依頼 — C2 コンテキスト仮想化と是正スライス

この文書は、別のAIレビュアーにそのまま渡せる依頼文である。

対象は二つある。**PR #102 の設計そのもの**と、**その監査中に発見された欠陥に対する是正実装**である。
後者は既に production code に適用済みであり、これも監査対象に含める。

---

## 0. 依頼文（そのまま貼り付け可）

> souten-yd/ExtendCodeAgent を独立監査してください。
>
> 対象は次の2つです。
>
> 1. Draft PR #102 `agent/context-virtualization-semantic-working-set`（設計文書のみ、+1745行）
> 2. ブランチ `agent/weak-local-evidence-protocol` に適用済みの是正実装
>    （`docs/handoff/C2_TRUTH_SCOPE_AND_COST_FIDELITY_CORRECTIVE_DESIGN.md` 参照）
>
> **設計文書・監査文書のいずれも、実装済みの事実として信用しないでください。**
> `src/extendcodeagent/` の production code、`tests/`、`docs/evidence/` の実測値を直接確認し、
> 文書の主張と実装の乖離を報告してください。
>
> 先行監査は結論を `NARROW_AND_RETEST` としています。この結論に同意することが目的ではありません。
> 先行監査自体が誤っている、あるいは是正実装が新たな問題を作っている場合は、そう指摘してください。
>
> 最終的に `ADOPT_AS_DESIGNED` / `ADOPT_WITH_CHANGES` / `NARROW_AND_RETEST` / `REJECT` のいずれかと、
> 次に merge を許可すべき最小実装スライスを提示してください。

---

## 1. 事前に読むべきもの（この順序で）

| 順 | 文書 | 役割 |
|---|---|---|
| 1 | `AGENTS.md` | 不変ポリシー。特に「切れない機構は価値を証明できない」 |
| 2 | `docs/PI_MASTER_EXECUTION_PLAN.md` §5, §6, §8 Phase 2 | 正式なバックログと capability 台帳。C2 の正規スコープ |
| 3 | `docs/handoff/C2_EVIDENCE_DELIVERY_DECISION.md` | **merge 済みの C2 決定**。PR #102 との重複判定の基準 |
| 4 | PR #102 の3文書 | 監査対象の設計 |
| 5 | `docs/audit/C2_CONTEXT_VIRTUALIZATION_INDEPENDENT_AUDIT.md` | 先行監査。**これも疑ってよい** |
| 6 | `docs/handoff/C2_TRUTH_SCOPE_AND_COST_FIDELITY_CORRECTIVE_DESIGN.md` | 是正設計と残存ギャップ G-1〜G-6 |

---

## 2. 検証してほしい既存コード所有者

PR #102 の各新概念について、以下の既存所有者と重複していないかを **コードを読んで** 判定してください。

| 領域 | ファイル | 既に持っているもの |
|---|---|---|
| Graph / Twin | `graph/contracts.py`, `twin/lifecycle.py`, `twin/source_snapshot.py` | 不変ノード/エッジ、リビジョン、無効化、解析器バージョン |
| Verification | `verification/contracts.py` | `SemanticChangeSet`, `VerificationObligation`(7種), `RequiredVerificationSet`, criticality |
| TaskSignals / Plan | `orchestration/contracts.py` | `TaskSignals`, `TaskIntent`(13種), `IntelligencePlan`, `ContextScope`, `PlanOutcome` |
| Runtime | `runtime/contracts.py` | `RuntimeObservation`, `RuntimeCapabilities`, `ReconciliationOutcome` |
| Traceability | `traceability/contracts.py` | 要求→実装証跡 |
| Blueprint / Convergence | `blueprint/contracts.py`, `convergence/contracts.py` | 計画要素、target/actual/verification、7状態×7決定 |
| Storage | `storage/sqlite.py` | bitemporal (`valid_from`/`valid_to`)、workspace scope、単一DB |
| Context | `context/contracts.py`, `context/service.py`, `context/serialization.py` | `ContextPackage`、`WeakLocalEvidencePackage`、`EvidenceScope`、コスト推定 |

各新概念に `REUSE` / `EXTEND` / `PROJECT` / `CONSOLIDATE` / `NEW` のいずれかを付し、
`NEW` には既存所有者で満たせない理由を必ず添えてください。

---

## 3. 重点的に反証してほしい論点

### 3.1 先行監査の主張の再検証（最優先）

先行監査は次の2つを P0 欠陥として報告し、修正しました。**再現手順を実行して真偽を確認してください。**

**(a) Twin がプロジェクト自身を索引していなかった**

```bash
git stash                       # 是正前の状態に戻す
python3 - <<'PY'
from pathlib import Path
IGN={".git",".hg",".svn",".venv","venv","node_modules","dist","build",
     "__pycache__",".pytest_cache",".mypy_cache",".ruff_cache",".extendcodeagent"}
root=Path.cwd(); n=0; per={}
for p in sorted(root.rglob("*")):
    if not p.is_file(): continue
    rel=p.resolve().relative_to(root)
    if any(x.lower() in IGN or x.lower().endswith(".egg-info") for x in rel.parts): continue
    per[rel.parts[0]]=per.get(rel.parts[0],0)+1; n+=1
print("total", n); print(sorted(per.items(), key=lambda x:-x[1])[:6])
PY
git stash pop
```

確認事項:

- `.evaluation/` は `.gitignore` に記載があるが `IGNORED_NAMES` には無い。これは意図的な設計か、抜けか
- `max_files=10_000` の打ち切りが `INFO` 診断だったことの妥当性
- `docs/evidence/final/` の既存成果物のうち、この欠陥の影響を受けているものはどれか
  （評価ランナーは corpus を別 workspace に複製するため、B0b の 93,189 tokens は影響外と先行監査は判断している。**この切り分けは正しいか**）
- 是正手段として `git ls-files --exclude-standard` を使うことの副作用
  （非 Git ルート、submodule、sparse checkout、巨大 worktree、subprocess 依存の増加）

**(b) トークン予算が配信ペイロードを測っていなかった**

`context/service.py::_context_item` の是正前後を比較し、5.1倍の過小評価という主張を検証してください。
特に **不動点ループ（最大3回）が本当に収束するか**、収束しない入力が存在しないかを確認してください。

### 3.2 32k / 64k 目標の実現可能性

- `docs/evaluation/large-project-bounded-context-target-v1.json` の
  `required_supported_profile_max_tokens: 65536` は「出力ヘッドルームを含む総量」と定義されている。
  現在の実装でこの総量を観測できるか。できないなら、目標は検証不能ではないか
- 是正後の実測（symbol タスク: candidate 70、gap 0、推定誤差 1.01倍）は
  32k p95 の根拠として十分か。3タスクのサンプルで何が言えて何が言えないか
- `_infer_scope` が全タスクで `verification` を返す（G-2）状態で、
  scope ladder による段階的拡大は機能していると言えるか

### 3.3 Semantic Contract / ABI の false negative

- `graph/analyzers/python.py` と `javascript_typescript.py` が実際に emit する
  プロパティ/エッジ種別を列挙してください
- PR #102 §6.1 の16フィールドのうち、**今日機械的に導出できるのは何個か**
- 導出不能フィールドが `unknown` として fingerprint に入る場合、
  fingerprint はどの程度の頻度で「境界不変」を誤報告するか
- 先行監査は「shadow 限定、public boundary の false_stop_rate = 0 を要求、C2 から外す」としている。
  この緩和条件で十分か、過剰か

### 3.4 Memory の stale / invalidation

- `storage/sqlite.py` の bitemporal 構造は memory の永続化に十分か
- PR #102 §9.1 の「構造メモリ」は Graph/Twin から再生成されるなら
  それは cache であって memory ではない、という先行監査の指摘は妥当か
- 「決定メモリ」はファイル変更では陳腐化しない。何が invalidation key になり得るか
- `CapabilityName.MEMORY` は既に宣言され `not_implemented` で強制 `off`。
  設計はこの既存 capability に接続していないが、問題か

### 3.5 Task Engine 新設の必要性

- `orchestration.PlanOutcome` + `convergence` + `blueprint` の組合せで
  `TaskExecutionState` の最小フィールドをどこまで表現できるか
- 「セッション履歴が実行進捗の復元に必要」という測定は repository 内に存在するか
- 存在しないなら、C2-9 に置くことすら正当化されるか

### 3.6 Context Compiler の責任分離

- PR #102 §13.1 の7モジュール分割は、451行のサービスに対して過剰ではないか
- 是正実装が行った2分割（`context/serialization.py`、`testing/selection.py`）は
  適切な粒度か。逆に分割不足/過剰な箇所はあるか

### 3.7 保守性

- `service/application.py` (1,533行) — 是正で219行削減されたが、なお facade として妥当か
- `tools/local/evaluation_runner.py` (2,811行)、`adaptive_screening_runner.py` (1,801行) —
  production より大きい評価ツールのリスク評価
- `tests/architecture/test_application_facade.py` の line budget 方式は
  有効な強制手段か、それとも回避が容易な見せかけか

### 3.8 ガバナンス

- Master Plan §8 は C2 を **conditional** な単一ステージと定義している。
  PR #102 は9サブステージに拡張している。これは範囲逸脱か、正当な精緻化か
- PR #102 の3文書に `CapabilityName` / `CapabilityPolicy` / `ablation` の出現が **0回** である。
  AGENTS.md の不変条件との整合をどう評価するか
- 直近40コミットで `docs/` 111回 対 `src/` 17回、docs 14,999行 対 src 13,004行。
  B0b は Graph/Twin/Semantic/Test Selection を `NO_CONFIRMED_CAUSAL_EFFECT` と記録している。
  この状況で更に1,745行の設計を追加することの妥当性

---

## 4. 是正実装そのものへの反証依頼

以下は**先行監査が自ら加えた変更**である。利害関係者による変更なので、特に厳しく見てほしい。

| 変更 | 疑うべき点 |
|---|---|
| `_candidate_paths()` の `git ls-files` 依存 | subprocess 失敗時の静かなフォールバック、timeout 30秒の妥当性、`--others` が未追跡ファイルを含めることの是非 |
| `SOURCE_SNAPSHOT_VERSION` を `v2` へ | 既存 Twin リビジョンの互換性、`docs/evaluation/b0a-checkpoint-compatibility-*.json` への影響 |
| `file_limit` を `ERROR` へ昇格 | `ERROR` 診断を消費する側が本当に失敗扱いにするか。単に severity が変わっただけで挙動は同じでは |
| 推定不動点ループ | 3回で足りない入力の存在、`replace()` によるオブジェクト再生成コスト |
| `testing/selection.py` への移動 | 純粋な移動か、挙動が変わっていないか。`REQUIRED_OBLIGATIONS` を frozenset 化した影響 |
| facade line budget = 1,600 | 恣意的な数値ではないか。ratchet が実際に下がる保証はあるか |

---

## 5. 再現コマンド

```bash
python -m pytest -q                                    # 329 tests
ruff check src/ tests/ && ruff format --check src/ tests/
mypy src/                                              # 75 files

# C2 preflight（ROOT に対して実行される。出力先はリポジトリ外を推奨）
python tools/local/c2_evidence_protocol.py --output /tmp/c2-after.json
```

`tools/local/c2_evidence_protocol.py` は未追跡ファイルである点に注意。既定の出力先は
`docs/evidence/final/c2-weak-local-protocol-preflight-v1.json` で、**是正前の Twin で実行すると
無効な成果物を封印してしまう**。

---

## 6. 求める成果物

1. **否定的所見を先に**。同意できる点は後で簡潔に
2. 各新概念の `REUSE`/`EXTEND`/`PROJECT`/`CONSOLIDATE`/`NEW` 分類（根拠はファイル:行で）
3. 先行監査の P0 主張2件それぞれについて **CONFIRMED / PLAUSIBLE / REFUTED**
4. 是正実装が導入した新たなリスクの列挙
5. 32k/64k について「現時点で言えること」と「言えないこと」の分離
6. **より小さいアーキテクチャで80%の効果が得られるなら、その提案**
   （先行監査は「正しい Twin + 正直なコストモデル + 既存 obligation + AnswerIR の4点で足りる」と主張している。
   これに反証または対案を）
7. 最終判定と、次に merge を許可すべき最小実装スライス

## 7. 禁止事項

- 設計文書の記述を実装の証拠として引用しないこと
- 目標が魅力的であることを理由に承認しないこと
- 先行監査の結論に追従することを目的としないこと
- 「概ね妥当」で終わらせないこと。反証が見つからなかったなら、探した範囲を明示すること
