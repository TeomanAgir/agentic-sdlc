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
- Ne oldu: (kurulum sonrası doldurulacak)
- Tasarım kararı: planın aksine, label geçişleri agent'lara değil workflow
  adımlarına verildi (`gh issue edit` step'leri). Gerekçe: geçişler
  deterministik olmalı; agent'ın label'ı unutması/yanlış label eklemesi
  state machine'i bozar. Agent yalnızca içerik üretir; workflow, agent adımı
  başarılıysa sonraki label'ı ekler, başarısızsa `agent:blocked` ekler.
- Sonuç / ders: (doldurulacak)
