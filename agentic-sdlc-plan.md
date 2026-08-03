# Agentic SDLC — Choreography Deneyi: Uygulama Planı

> Bu dosya Claude Code'a verilecek yürütme planıdır. Fazlar sıralıdır; her fazın
> kabul kriterleri sağlanmadan sonrakine geçilmez. Sorulması gereken kararlar
> "AÇIK KARAR" olarak işaretlidir — bunları uygulamadan önce kullanıcıya sor.

## 1. Amaç ve Kapsam

Amaç: SDLC aşamalarını (review, planlama, implementasyon, CI triage) headless
agent'larla otomatize eden, **choreography** desenli bir deney repo'su kurmak.

Temel ilkeler:
- Agent'lar birbirleriyle **doğrudan konuşmaz**. Tüm iletişim GitHub
  artefaktları üzerinden yürür: issue, PR, comment, label, workflow event.
- Merkezi orchestrator ve queue **yok**. Her agent, bir GitHub event'i ile
  tetiklenen bağımsız bir workflow job'ıdır.
- Her adımda insan onay noktası (human-in-the-loop) label veya PR approve ile
  temsil edilir.
- Her agent koşusu izlenebilir olmalı: tam log artifact olarak saklanır.

Kapsam dışı (bu deneyde yapılmayacak): orchestrator agent, mesaj kuyruğu,
cross-repo tetikleme, production deploy otomasyonu.

## 2. Mimari

### 2.1 İletişim omurgası: GitHub-as-bus

```
issue açılır ──▶ [Planner Agent] ── plan comment + label ──▶ insan onayı (label)
                                                                    │
                                                                    ▼
                                                        [Implementer Agent]
                                                                    │
                                                              PR açar
                                                                    ▼
PR event ──▶ [Reviewer Agent] ── review comment ──▶ insan merge kararı
                                                                    │
CI fail ──▶ [Triage Agent] ── root-cause comment ◀── workflow_run  ◀┘
```

### 2.2 State machine (label'lar)

Label'lar tek doğruluk kaynağıdır (ground truth). Bir issue/PR'ın hangi
aşamada olduğu yalnızca label'larından okunur.

| Label | Anlamı | Kim ekler |
|---|---|---|
| `agent:needs-plan` | Planner tetiklenmeli | İnsan (issue açarken) |
| `agent:plan-ready` | Plan yazıldı, onay bekliyor | Planner agent |
| `agent:plan-approved` | Implementer tetiklenmeli | İnsan |
| `agent:in-progress` | Implementer çalışıyor | Implementer agent |
| `agent:needs-review` | PR açıldı, review bekliyor | Implementer agent |
| `agent:blocked` | Agent başarısız, insan gerekli | Herhangi bir agent |

Kural: bir agent yalnızca **kendi giriş label'ı** varsa çalışır ve bittiğinde
kendi label'ını kaldırıp bir sonrakini ekler. Bu, event fırtınası ve çift
tetiklenmeyi engeller (idempotency).

### 2.3 Agent çalıştırma mekanizması

İki seçenek, ikisi de aynı motoru (Claude Code headless) kullanır:

1. **`anthropics/claude-code-action@v1`** (varsayılan): GitHub context'i,
   auth'u ve comment/commit/PR mekaniklerini kendisi yönetir. `prompt`
   parametresi verilirse automation modunda headless koşar; verilmezse
   `@claude` mention'larına yanıt verir. CLI bayrakları `claude_args` ile
   geçilir (`--max-turns`, `--allowedTools`, `--model` vb.).
2. **Ham `claude -p "<prompt>"`**: Herhangi bir runner'da shell komutu olarak
   koşar; `--output-format json` ile makine-okunur çıktı verir, exit code ile
   pipeline dallanır. Action'ın esnek gelmediği yerlerde (ör. Triage Agent'ın
   sadece comment atması) kullanılabilir.

AÇIK KARAR: API key mi, mevcut Claude aboneliği mi kullanılacak? Repository
secret olarak `ANTHROPIC_API_KEY` gerekiyorsa kullanıcıdan iste. Kurulum
kolaylığı için `claude` içinde `/install-github-app` komutu GitHub App +
secret kurulumunu uçtan uca yapar — Faz 0'da bunu öner.

## 3. Repo Yapısı

```
agentic-sdlc/
├── CLAUDE.md                  # Tüm agent'ların ortak anayasası
├── README.md                  # Deneyin amacı + mimari özeti
├── RUNBOOK.md                 # Operasyon notları, secret expiry, bilinen hatalar
├── .github/
│   └── workflows/
│       ├── planner.yml        # Faz 2
│       ├── implementer.yml    # Faz 3
│       ├── reviewer.yml       # Faz 1
│       ├── triage.yml         # Faz 4
│       └── ci.yml             # Uygulamanın kendi test pipeline'ı
├── prompts/
│       ├── planner.md         # Agent'a verilen görev şablonu
│       ├── implementer.md
│       ├── reviewer.md
│       └── triage.md
└── app/                       # Üzerinde çalışılacak örnek uygulama
```

Neden `prompts/` ayrı klasör: prompt'lar workflow YAML'ına gömülürse diff'i
okunmaz hale gelir; ayrı dosyada versiyonlanır, review edilir, agent
davranış değişiklikleri commit history'de izlenir.

AÇIK KARAR: `app/` içine ne konacak? Öneri: kasıtlı olarak küçük bir REST API
(tercihen kullanıcının bildiği bir stack) — agent'ların üzerinde
çalışabileceği gerçekçi ama sınırlı bir yüzey. Kullanıcıya sor.

## 4. Faz 0 — Bootstrap

Yapılacaklar:
1. Repo'yu oluştur, `main` branch protection: direct push kapalı, PR zorunlu,
   en az 1 insan approval, status check zorunlu.
2. Bölüm 2.2'deki label'ları oluştur (`gh label create ...`).
3. `CLAUDE.md` yaz. İçermesi gerekenler:
   - Kod standartları (dil, stil, test zorunluluğu)
   - Agent davranış kuralları: "asla main'e push etme", "her değişiklik için
     branch + PR", "belirsizlikte `agent:blocked` label'ı ekle ve dur"
   - Commit mesaj formatı ve PR description şablonu
4. `RUNBOOK.md` iskeleti: secret'lar, expiry tarihleri, manuel müdahale
   prosedürleri. (Önceki PAT-expiry takip pratiğinin aynısı.)
5. Auth kurulumu: `/install-github-app` veya manuel `ANTHROPIC_API_KEY`
   secret'ı + `examples/claude.yml` tabanlı workflow.
6. `app/` iskeletini ve `ci.yml`'i (lint + test) kur.

Kabul kriteri: `ci.yml` yeşil koşuyor; main'e direct push reddediliyor;
label'lar mevcut.

## 5. Faz 1 — Reviewer Agent (en düşük risk, ilk kurulacak)

Neden ilk bu: yazma yetkisi yalnızca comment/review; kod değiştirmez.
Pipeline mekanikleri (tetikleme, permission, log) düşük riskle doğrulanır.

`reviewer.yml` iskeleti:

```yaml
name: reviewer-agent
on:
  pull_request:
    types: [opened, synchronize]
permissions:
  contents: read
  pull-requests: write
  issues: write
concurrency:
  group: reviewer-${{ github.event.pull_request.number }}
  cancel-in-progress: true
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            prompts/reviewer.md dosyasındaki talimatları uygula.
            PR: #${{ github.event.pull_request.number }}
          claude_args: |
            --max-turns 15
            --allowedTools "Read,Grep,Glob,Bash(gh pr view:*),Bash(gh pr diff:*),Bash(gh pr comment:*)"
```

`prompts/reviewer.md` içeriği (özet): diff'i oku, CLAUDE.md standartlarına
göre değerlendir; bulguları önem sırasıyla (blocker/major/minor) tek bir PR
comment'inde raporla; kod değiştirme; emin olmadığın konuda soru sor.

Kabul kriterleri:
- Test PR'ına anlamlı, önem-sıralı review comment'i geliyor.
- Aynı PR'a push gelince eski koşu iptal olup yenisi başlıyor (concurrency).
- Agent'ın kod değiştirme girişimi yok (allowedTools bunu zaten engelliyor —
  log'dan doğrula).

## 6. Faz 2 — Planner Agent

Tetik: `issues` event'i, `labeled` tipi, label `agent:needs-plan`.

Akış:
1. Issue body'sini ve repo'daki ilgili dosyaları oku (Read/Grep — yazma yok).
2. Plan üret: kapsam, değişecek dosyalar, test stratejisi, riskler,
   tahmini adımlar.
3. Planı issue'ya comment olarak yaz.
4. `agent:needs-plan` label'ını kaldır, `agent:plan-ready` ekle.
5. Plan üretilemiyorsa (belirsiz issue): eksik bilgiyi soran comment +
   `agent:blocked`.

Workflow'da `if: github.event.label.name == 'agent:needs-plan'` guard'ı
zorunlu — her label event'inde koşmasın.

Kabul kriteri: label eklenince plan geliyor, label geçişi doğru işliyor,
alakasız label'lar tetiklemiyor.

## 7. Faz 3 — Implementer Agent (ilk yazma yetkili agent)

Tetik: `agent:plan-approved` label'ı eklenince.

Akış:
1. Issue'daki onaylı planı comment'lerden oku (context assembly — bkz. §9).
2. `agent/issue-<no>` branch'i aç.
3. Planı uygula; testleri **lokal olarak koştur ve geçir** (test-before-commit
   guard'ı — kırık kodla PR açma).
4. PR aç: description'da plana ve issue'ya link; `agent:needs-review` label'ı.
5. Herhangi bir adımda başarısızlık → `agent:blocked` + açıklayıcı comment.

Guardrail'ler:
- `permissions: contents: write` yalnızca bu workflow'da; branch protection
  main'i zaten koruyor.
- `--max-turns` sıkı tutulur (öneri: 40); aşılırsa `agent:blocked`.
- `allowedTools` içinde `Bash` geniş verilmez; test/build komutları explicit
  pattern'lerle whitelist'lenir.

Kabul kriteri: onaylı bir issue'dan, testleri geçen, Reviewer Agent'ın da
review'ladığı bir PR uçtan uca üretiliyor. (Faz 1 + Faz 3 burada zincirlenir:
Implementer'ın PR'ı Reviewer'ı event ile tetikler — choreography'nin ilk
gerçek kanıtı.)

## 8. Faz 4 — Triage Agent

Tetik: `workflow_run` (ci.yml, `conclusion == 'failure'`) — yalnızca agent
branch'lerinde veya PR'larda.

Akış: failed run'ın log'unu `gh run view --log` ile çek → root cause analizi →
ilgili PR'a comment: hata özeti, muhtemel neden, önerilen fix. Kod değiştirmez
(bu deneyde otomatik fix kapsam dışı; bir sonraki iterasyonda Implementer'a
"fix" görevi devretme label'ı eklenebilir).

Kabul kriteri: kasıtlı kırılan bir testte, doğru root cause'u işaret eden
comment üretiliyor.

## 9. Context Assembly Kuralları (kritik)

Her agent sıfır hafızayla başlar. Prompt şablonları şu sırayla context kurar:

1. `CLAUDE.md` (action bunu otomatik okur — kurallar burada yaşar)
2. Tetikleyen artefakt: issue body / PR diff / failure log
3. İlgili geçmiş: issue'daki onaylı plan comment'i (Implementer için),
   önceki review bulguları (ikinci tur review için)
4. Görev tanımı: `prompts/<agent>.md`

Kural: agent'a "repo'nun tamamını oku" denmez; Grep/Glob ile hedefli keşif
istenir. Context şişmesi hem maliyeti hem kaliteyi bozar.

## 10. Gözlemlenebilirlik ve Maliyet

- Her workflow, agent'ın tam transcript'ini (`--output-format json` çıktısı
  veya action log'u) artifact olarak yükler (retention: 30 gün).
- `--max-turns` tüm agent'larda zorunlu; workflow `timeout-minutes` set edilir
  (öneri: reviewer/planner 10, implementer 30).
- `concurrency` grubu tüm workflow'larda tanımlı — aynı artefakt için paralel
  koşu yok.
- RUNBOOK.md'ye haftalık maliyet gözlem notu bölümü ekle.

## 11. Deney Günlüğü

Repo köküne `EXPERIMENTS.md`: her fazda ne beklendi / ne oldu / hangi prompt
değişikliği neyi düzeltti. Bu deneyin asıl çıktısı kod değil, bu gözlemler.

## 12. Fazlara Bağlı Yol Haritası (özet)

| Faz | Çıktı | Bağımlılık |
|---|---|---|
| 0 | Repo + guardrails + auth | — |
| 1 | Reviewer Agent | Faz 0 |
| 2 | Planner Agent | Faz 0 |
| 3 | Implementer Agent | Faz 1, 2 |
| 4 | Triage Agent | Faz 3 (agent PR'ları üzerinde anlamlı) |

## 13. Doğrulama Kaynakları

Uygulama sırasında güncel referanslar:
- Claude Code GitHub Actions dokümantasyonu: https://code.claude.com/docs/en/github-actions
- Action repo'su ve örnekler: https://github.com/anthropics/claude-code-action
- Headless mod (`claude -p`) CLI referansı: https://docs.claude.com/en/docs/claude-code/overview
