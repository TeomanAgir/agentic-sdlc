# agentic-sdlc — Choreography Deneyi

SDLC aşamalarını (planlama, implementasyon, review, CI triage) headless
agent'larla otomatize eden bir deney repo'su. Desen: **choreography** —
merkezi orchestrator yok, agent'lar birbiriyle doğrudan konuşmaz; tüm
iletişim GitHub artefaktları (issue, PR, comment, label, workflow event)
üzerinden yürür.

## Mimari

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

Temel ilkeler:

- **GitHub-as-bus**: her agent, bir GitHub event'i ile tetiklenen bağımsız bir
  workflow job'ıdır.
- **Label = state machine**: bir issue/PR'ın aşaması yalnızca label'larından
  okunur (tablo: `CLAUDE.md`). Label geçişleri deterministik workflow
  adımlarıyla yapılır; agent'lar yalnızca içerik üretir.
- **Human-in-the-loop**: plan onayı (`agent:plan-approved` label'ı) ve PR
  merge kararı insanda.
- **İzlenebilirlik**: her agent koşusunun tam log'u workflow artifact'ı
  olarak 30 gün saklanır.

## Bileşenler

| Yol | Ne |
|---|---|
| `CLAUDE.md` | Tüm agent'ların ortak anayasası |
| `prompts/` | Agent görev şablonları (versiyonlanır, review edilir) |
| `.github/workflows/planner.yml` | Issue'ya `agent:needs-plan` eklenince plan üretir |
| `.github/workflows/implementer.yml` | `agent:plan-approved` eklenince branch + PR üretir |
| `.github/workflows/reviewer.yml` | PR açılınca/güncellenince review comment'i yazar |
| `.github/workflows/triage.yml` | CI fail olunca root-cause comment'i yazar |
| `.github/workflows/ci.yml` | Uygulamanın lint + test pipeline'ı |
| `app/` | Örnek uygulama: FastAPI Notes API |
| `EXPERIMENTS.md` | Deney günlüğü — asıl çıktı |
| `RUNBOOK.md` | Operasyon notları, secret'lar, manuel müdahale |

## Kullanım (mutlu yol)

1. Issue aç, `agent:needs-plan` label'ını ekle → Planner plan comment'i yazar,
   label `agent:plan-ready` olur.
2. Planı beğendiysen `agent:plan-approved` label'ını ekle → Implementer
   branch açar, planı uygular, testleri geçirir, PR açar.
3. PR açılınca Reviewer otomatik review comment'i yazar.
4. CI kırmızıysa Triage PR'a root-cause comment'i yazar.
5. Merge kararı senin.

Ayrıntılı plan: `agentic-sdlc-plan.md`.
