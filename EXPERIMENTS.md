# EXPERIMENTS — Deney Günlüğü

Bu deneyin asıl çıktısı kod değil, buradaki gözlemler. Her kayıt şu şablonu
kullanır:

```
## <tarih> — <faz / deneme adı>
- Beklenti:
- Ne oldu:
- Prompt/konfig değişikliği:
- Sonuç / ders:
```

---

## 2026-08-03 — Faz 0: Bootstrap

- Beklenti: repo + label'lar + branch protection + yeşil CI.
- Ne oldu: `TeomanAgir/agentic-sdlc` (public) oluşturuldu. CI ilk push'ta
  yeşil (run 30794911518). Direct push GH006 ile reddedildi (PR + "test"
  status check zorunlu, enforce_admins açık). 6 `agent:*` label'ı mevcut.
- Öğrenilen: `/install-github-app`, abonelik hesabında `ANTHROPIC_API_KEY`
  değil `CLAUDE_CODE_OAUTH_TOKEN` secret'ı oluşturuyor; action her iki input'u
  da destekliyor (`action.yml` doğrulandı). Workflow'lara ikisi de fallback'li
  eklendi.
- Öğrenilen kısıt: varsayılan `github.token` ile yapılan push/PR başka
  workflow tetiklemez (GitHub recursion koruması). Implementer → Reviewer/CI
  zinciri için `AGENT_GITHUB_PAT` secret'ı şart; workflow'lar
  `AGENT_GITHUB_PAT || github.token` fallback'iyle yazıldı.
- Tasarım kararı: planın aksine, label geçişleri agent'lara değil workflow
  adımlarına verildi (`gh issue edit` step'leri). Gerekçe: geçişler
  deterministik olmalı; agent'ın label'ı unutması/yanlış label eklemesi
  state machine'i bozar. Agent yalnızca içerik üretir; workflow, agent adımı
  başarılıysa sonraki label'ı ekler, başarısızsa `agent:blocked` ekler.
- Sonuç / ders: (doldurulacak)
