# RUNBOOK — Operasyon Notları

## Secret'lar ve expiry takibi

| Secret / Kurulum | Nerede | Amaç | Expiry | Son kontrol |
|---|---|---|---|---|
| Claude GitHub App | Repo installation | claude-code-action'ın GitHub auth'u (comment, push, PR) | — (app installation, süresiz) | (kurulumda doldur) |
| `CLAUDE_CODE_OAUTH_TOKEN` | Repository secret | claude-code-action'ın Anthropic auth'u (abonelik; `/install-github-app` oluşturdu) | bilinmiyor — token hata verirse `/install-github-app`'i tekrar çalıştır | 2026-08-03 |
| `ANTHROPIC_API_KEY` | Repository secret (opsiyonel) | Abonelik yerine API key kullanılacaksa alternatif auth | (key oluştururken doldur) | — (tanımlı değil) |
| `AGENT_GITHUB_PAT` | Repository secret | Implementer'ın push/PR'ının ci + reviewer workflow'larını **tetikleyebilmesi** (varsayılan `github.token` ile yapılan push/PR, GitHub recursion koruması nedeniyle event tetiklemez) | ~2026-11-01 (90 günlük; GitHub ayarlarından teyit et, 1 hafta önce yenile) | 2026-08-03 — ilk token terminale düz metin girdiği için rotate edildi |

Kural: expiry'si olan her secret bu tabloya eklenir; expiry'den 1 hafta önce
yenile. Secret yenilenince "Son kontrol" sütununu güncelle.

## Kurulum

1. Lokalde `claude` içinde `/install-github-app` çalıştır → GitHub App'i
   `agentic-sdlc` repo'suna kurar; abonelik hesabında `CLAUDE_CODE_OAUTH_TOKEN`
   secret'ını ekler (API hesabında `ANTHROPIC_API_KEY`). ✅ 2026-08-03 yapıldı.
2. Doğrulama: `gh secret list` çıktısında ilgili secret görünmeli;
   repo Settings → GitHub Apps altında Claude app görünmeli.
3. Fine-grained PAT oluştur (yalnızca bu repo; Contents: read/write,
   Pull requests: read/write, Issues: read/write) ve secret olarak ekle:
   `gh secret set AGENT_GITHUB_PAT`. Bu secret yoksa akış çalışır ama
   Implementer'ın açtığı PR'lar ci/reviewer'ı otomatik tetiklemez
   (manuel tetik: PR'ı kapatıp açmak).

## Manuel müdahale prosedürleri

### Agent `agent:blocked` bıraktı
1. İlgili issue/PR'daki `## Agent Blocked` comment'ini oku.
2. Sorunu gider (issue'yu netleştir, ortamı düzelt).
3. `agent:blocked` label'ını kaldır, akışı yeniden tetiklemek için ilgili
   giriş label'ını tekrar ekle (ör. `agent:needs-plan` / `agent:plan-approved`).

### Agent takıldı / koşu iptali
- `gh run list --workflow=<workflow>.yml` ile koşuyu bul,
  `gh run cancel <RUN_ID>`.
- Label state'ini elle tutarlı hâle getir (CLAUDE.md'deki tabloya göre).

### Agent yanlış/istenmeyen değişiklik push'ladı
- `main` korumalıdır; merge edilmemişse PR'ı kapat, branch'i sil:
  `git push origin --delete agent/issue-<no>`.

### Yeniden tetikleme
- Planner/Implementer: giriş label'ını kaldırıp tekrar ekle.
- Reviewer: PR'a boş commit push'la veya PR'ı kapat/aç.
- Triage: failed CI run'ı `gh run rerun <RUN_ID>` ile tekrarla.

## Bilinen hatalar / notlar

- (boş — deney sırasında doldurulacak)

## Haftalık maliyet gözlemi

| Hafta | Koşu sayısı (agent bazında) | Yaklaşık maliyet | Not |
|---|---|---|---|
| | | | |
