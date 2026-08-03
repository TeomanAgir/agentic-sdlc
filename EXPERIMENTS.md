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

## 2026-08-03 — Faz 1: Reviewer Agent canlı testleri

- Beklenti: PR açılınca reviewer önem-sıralı review comment'i yazar.
- Ne oldu (deneme 1, PR #2): action `id-token: write` izni olmadan OIDC token
  alamayıp düştü → izin dört workflow'a eklendi.
- Ne oldu (deneme 2, PR #2): action, PR'da değiştirilen workflow dosyasını
  güvenlik gereği çalıştırmayı reddetti ("must be identical to default
  branch") ve koşu sessizce "success" bitti. Ders: agent workflow
  değişiklikleri ancak main'e merge edildikten sonra canlı test edilebilir;
  "success" her zaman "çalıştı" demek değil, log'daki "Auto-detected mode" /
  "Skipping action" satırlarını kontrol et.
- Ne oldu (deneme 3, PR #3): auth ve tetikleme çalıştı; agent 16 turn'de
  6 izin reddiyle comment atamadan `error_max_turns` ile düştü
  (maliyet ~$0.32). Hipotez: uzun comment gövdesini dosyaya yazmaya çalıştı,
  Write izni yoktu.
- Prompt/konfig değişikliği: reviewer/planner/triage'a `Write` izni eklendi
  (contents: read olduğundan push riski yok); prompt'lara "gövdeyi /tmp'ye
  Write ile yaz, `--body-file` ile gönder" talimatı; turn limitleri
  15→25/20/20.
- Sonuç / ders (deneme 4): ✅ Faz 1 kabul kriterlerinin tümü sağlandı.
  Reviewer, PR #3'teki kasıtlı bug'ı (type hint eksikliği → path param `str`
  kalıp her zaman 404) Blocker olarak dosya:satır referansıyla yakaladı;
  test eksikliğini CLAUDE.md'ye bağladı. Bulgular uygulanınca ikinci review,
  önceki bulguların düzeltildiğini madde madde teyit etti (context assembly
  çalışıyor: eski comment'leri okuyor). Concurrency: art arda iki push'ta
  ilk koşu `cancelled` oldu (run 30796863597). Transcript artifact'ı
  yüklendi (30 gün retention). Agent'ın kod değiştirme girişimi yok.
  Maliyet gözlemi: review başına ~$0.30.

## 2026-08-03 — Faz 2: Planner Agent canlı testi

- Beklenti: `agent:needs-plan` label'ı plan comment'i üretir, label
  `agent:plan-ready`'ye geçer, alakasız label'lar tetiklemez.
- Ne oldu: Issue #5 (GET /notes ?q= araması) label'la açıldı; planner tek
  koşuda doğru formatta plan yazdı (kapsam / değişecek dosyalar / test
  stratejisi / adımlar) ve label geçişi workflow step'iyle doğru işledi.
  Negatif test: alakasız `docs` label'ı eklenince job guard'ı koşuyu
  `skipped` bıraktı — agent tetiklenmedi.
- Sonuç / ders: ✅ Faz 2 kabul kriterleri sağlandı. Write + `--body-file`
  akışı ilk denemede çalıştı — Faz 1'deki izin dersi doğrudan taşındı,
  planner hiç takılmadı.

## 2026-08-03 — Faz 3: Implementer Agent canlı testi

- Beklenti: `agent:plan-approved` → branch + testleri geçen PR +
  `agent:needs-review`; PR'ın reviewer/ci'ı event'le tetiklemesi
  (choreography kanıtı).
- Ne oldu (deneme 1): checkout'tan önce koşan `gh issue edit` adımı repo
  bağlamı bulamayıp düştü ("not a git repository"). Ders: checkout öncesi
  gh çağrılarına `GH_REPO` env'i şart.
- Ne oldu (deneme 2): ✅ Implementer planı uyguladı, testler yeşil, PR #8'i
  `claude` app'i olarak açtı; label geçişi temiz (`agent:needs-review`).
  **Choreography kanıtı**: PR #8, ci'ı (yeşil) ve reviewer'ı kendiliğinden
  tetikledi — `AGENT_GITHUB_PAT`/app token sayesinde event zinciri koptu
  kopmadı.
- Yeni engel: reviewer, tetikleyen aktör bot (`claude[bot]`) olduğu için
  koşmayı reddetti — action'ın güvenlik varsayılanı. Çözüm:
  `allowed_bots: "claude"` input'u (reviewer + triage).
- Sonuç / ders: agent→agent zincirlerinde bot aktör kısıtları da bir
  "iletişim protokolü" parçası; her yeni hop ilk seferde bir güvenlik
  varsayılanına çarpıyor ve bunlar tek tek açılmalı.
- Kapanış: `allowed_bots: "claude"` merge edildikten sonra reviewer,
  PR #8'i başarıyla review'ladı (Blocker/Major yok, 2 makul Minor).
  ✅ Faz 3 kabul kriteri uçtan uca sağlandı: issue → plan → insan onayı →
  implementer PR → reviewer, tamamen event zinciriyle.

## 2026-08-03 — Faz 4: Triage Agent canlı testi

- Beklenti: kasıtlı kırılan CI'da triage doğru kök nedeni işaret eden
  comment yazar.
- Ne oldu: PR #10'da `_next_id` artırma sırası kasıtlı bozuldu (lint
  geçer, 2 test kırılır). CI fail → `workflow_run` triage'ı tetikledi;
  triage tek koşuda tam isabet: artırma sırası → ilk not `id=2` →
  hangi iki testin neden kırıldığı, dosya:satır referanslı. Commit
  mesajından bunun kasıtlı bir test olduğunu bile tespit etti. Reviewer
  da aynı bug'ı bağımsız olarak Blocker'ladı (savunma katmanları
  örtüşüyor).
- Sonuç / ders: ✅ Faz 4 kabul kriteri sağlandı. Deneyin 4 fazı da
  tamamlandı; choreography deseni (GitHub-as-bus, label state machine,
  merkezi orchestrator'sız) uçtan uca çalışır durumda.
