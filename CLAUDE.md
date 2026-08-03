# CLAUDE.md — Agent Anayasası

Bu repo, SDLC aşamalarını headless agent'larla otomatize eden bir **choreography
deneyi**dir. Bu dosya tüm agent'ların (Planner, Implementer, Reviewer, Triage)
ortak kurallarını tanımlar. Buradaki kurallar prompt şablonlarındaki görev
tanımlarından önce gelir.

## Proje özeti

- `app/` — üzerinde çalışılan örnek uygulama: Python 3.12 + FastAPI ile küçük
  bir Notes REST API'si.
- `prompts/` — her agent'ın görev şablonu.
- `.github/workflows/` — agent'ları tetikleyen workflow'lar + `ci.yml`.

## Kod standartları

- Dil: Python 3.12, framework: FastAPI.
- Her davranış değişikliği test ile gelir; test yazılmadan kod değişikliği
  kabul edilmez. Testler `pytest` ile `app/` altında yaşar.
- Lint: `ruff check app` temiz olmalı.
- Public fonksiyonlarda type hint zorunlu.
- Test ve lint komutları:
  - `pip install -r app/requirements.txt`
  - `ruff check app`
  - `pytest app -q`

## Agent davranış kuralları

1. **Asla `main`'e push etme.** Her değişiklik `agent/issue-<no>` adlı bir
   branch'te yapılır ve PR ile gelir.
2. **Belirsizlikte dur.** Görev belirsizse, çelişkiliyse veya bir adım iki kez
   denendiği hâlde başarısızsa: durumu açıklayan bir comment yaz, işi bırak.
   (`agent:blocked` label'ı workflow tarafından eklenir.)
3. **Commit'ten önce test.** Testleri lokal koştur ve geçir; kırık kodla commit
   veya PR oluşturma.
4. **Kapsam dışına çıkma.** Yalnızca görevin gerektirdiği dosyalara dokun.
   `.github/workflows/`, `prompts/`, `CLAUDE.md` ve `RUNBOOK.md` dosyalarını
   issue açıkça istemedikçe değiştirme.
5. **Hedefli keşif.** Repo'nun tamamını okuma; Grep/Glob ile yalnızca görevle
   ilgili dosyaları bul ve oku.
6. **Label'lara dokunma.** Label geçişleri workflow adımları tarafından
   yönetilir; agent label ekleyip kaldırmaz.

## Commit mesaj formatı

```
<tip>: <kısa özet (emir kipi, ≤72 karakter)>

<gerekliyse gövde: ne ve neden>

Refs #<issue-no>
```

Tip: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`.

## PR description şablonu

```
## Ne
<değişikliğin özeti>

## Neden
Closes #<issue-no> — <issue başlığı>

## Plan
<issue'daki onaylı plan comment'ine link>

## Test
<hangi testler eklendi/koşuldu, sonuçları>
```

## Label state machine (tek doğruluk kaynağı)

| Label | Anlamı | Kim ekler |
|---|---|---|
| `agent:needs-plan` | Planner tetiklenmeli | İnsan (issue açarken) |
| `agent:plan-ready` | Plan yazıldı, onay bekliyor | Planner workflow |
| `agent:plan-approved` | Implementer tetiklenmeli | İnsan |
| `agent:in-progress` | Implementer çalışıyor | Implementer workflow |
| `agent:needs-review` | PR açıldı, review bekliyor | Implementer workflow |
| `agent:blocked` | Agent başarısız, insan gerekli | Workflow (agent adımı başarısız olunca) |
