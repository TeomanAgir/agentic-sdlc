# SETUP — Sistemi Sıfırdan Kurma Rehberi

Bu dosya, `agentic-sdlc` choreography sistemini **sıfırdan, hatalara
sürüklenmeden** yeniden kurmak için tek kaynaktır. Buradaki her adım,
ilk kurulumda canlı yaşanmış bir hatanın dersini içerir; dersler adımlara
gömülüdür, ayrıca sonda tam bir sorun giderme tablosu vardır.

Mimari özet için `README.md`, agent kuralları için `CLAUDE.md`, kurulum
sürecinin ham hikâyesi için `EXPERIMENTS.md`.

---

## 0. Ön koşullar

- `gh` CLI kurulu ve yetkili: `gh auth status` → `repo`, `workflow`
  scope'ları görünmeli.
- Claude aboneliği (Pro/Max) **veya** Anthropic API key.
- Lokal test için Python **3.12+** (kod `str | None` sözdizimi kullanır;
  3.9 ile `TypeError: unsupported operand type(s) for |` alırsınız —
  lokalde yoksa doğrulamayı CI'a bırakın).

## 1. Repo ve dosyalar

```bash
gh repo create <owner>/agentic-sdlc --public --clone
```

Bu repo'nun içeriğini aynen taşıyın (veya repo'yu template/fork olarak
kullanın). Kritik parçalar:

| Yol | Rol |
|---|---|
| `CLAUDE.md` | Agent anayasası — action bunu otomatik okur |
| `prompts/*.md` | Agent görev şablonları |
| `.github/workflows/{planner,implementer,reviewer,triage,ci}.yml` | Akış |
| `app/` | Üzerinde çalışılan uygulama (FastAPI Notes API) |
| `RUNBOOK.md`, `EXPERIMENTS.md` | Operasyon + deney günlüğü |

> **Ders (Faz 1.2):** Agent workflow'larında yapacağınız her değişiklik
> ancak **main'e merge edildikten sonra** canlı çalışır. `claude-code-action`,
> PR'da değiştirilen workflow dosyasını güvenlik gereği çalıştırmaz ve koşu
> **sessizce "success"** biter. Workflow'ları geliştirirken log'da
> "Skipping action due to workflow validation" satırını kontrol edin.

## 2. Label'lar (state machine)

```bash
gh label create "agent:needs-plan"    --color 0E8A16 --description "Planner tetiklenmeli (insan ekler)"
gh label create "agent:plan-ready"    --color FBCA04 --description "Plan yazıldı, onay bekliyor"
gh label create "agent:plan-approved" --color 1D76DB --description "Implementer tetiklenmeli (insan ekler)"
gh label create "agent:in-progress"   --color 5319E7 --description "Implementer çalışıyor"
gh label create "agent:needs-review"  --color C2E0C6 --description "PR açıldı, review bekliyor"
gh label create "agent:blocked"       --color B60205 --description "Agent başarısız, insan gerekli"
```

## 3. Branch protection + auto-merge

```bash
# main koruması: PR zorunlu, "test" status check'i zorunlu, approval 0
gh api -X PUT repos/<owner>/agentic-sdlc/branches/main/protection \
  -H "Accept: application/vnd.github+json" --input - <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["test"]},
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 0},
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

# Docs/fix PR'larının beklemeden akması için:
gh api -X PATCH repos/<owner>/agentic-sdlc -F allow_auto_merge=true
```

> **Ders:** Approval sayısını `1` yapmayın (tek kişilik repo'da). GitHub,
> PR yazarının kendi PR'ını approve etmesine izin vermez; `enforce_admins`
> açıkken admin bile bypass edemez → kendi PR'larınız **merge edilemez**
> hâle gelir. `0` ile PR + yeşil CI zorunluluğu korunur, merge kararı yine
> insandadır. (Agent PR'larını approve edebilirsiniz — onları bot açar.)

## 4. Auth: iki secret

### 4a. Claude auth — `/install-github-app`

Lokalde `claude` içinde `/install-github-app` komutunu çalıştırın:
GitHub App'i repo'ya kurar ve secret'ı ekler.

> **Ders:** Abonelik (Pro/Max) hesabında oluşan secret `ANTHROPIC_API_KEY`
> **değil** `CLAUDE_CODE_OAUTH_TOKEN`'dır. Workflow'lar bu yüzden iki
> input'u birden geçirir (boş olan yok sayılır):
> ```yaml
> anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
> claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
> ```
> Ayrıca komutun otomatik açtığı "Add claude GitHub actions" PR'ı bu
> kurulumda gereksizdir — kapatın (bizim workflow'larımız onun yerini alır).

### 4b. Agent zinciri — `AGENT_GITHUB_PAT`

Fine-grained PAT oluşturun (yalnızca bu repo; **Contents, Pull requests,
Issues: Read and write**), sonra:

```bash
gh secret set AGENT_GITHUB_PAT --body "github_pat_..."
```

> **Ders 1:** `gh secret set AD DEĞER` sözdizimi **yanlıştır**
> ("accepts at most 1 arg(s)" hatası). Değer `--body` ile ya da stdin'den
> verilir. Token'ı komut satırına yazdıysanız shell geçmişine düşmüştür —
> işiniz bitince rotate edin.
>
> **Ders 2 (kritik):** Bu secret olmadan zincir kopar. Workflow'un varsayılan
> `github.token`'ıyla açılan PR/push, GitHub'ın recursion koruması nedeniyle
> **başka workflow tetiklemez** — Implementer PR açar ama Reviewer ve CI
> sessizce hiç koşmaz. Workflow'lar `AGENT_GITHUB_PAT || github.token`
> fallback'i kullanır; PAT yoksa sistem "çalışıyor gibi" görünüp zincirin
> son halkasında kopar.

Doğrulama: `gh secret list` → iki secret da görünmeli.

## 5. Workflow'ların olmazsa olmazları (checklist)

Bu repo'daki workflow'lar bunların hepsini içerir; **sıfırdan yazacaksanız**
veya değiştirecekseniz şu listeyi koruyun — her madde canlı bir hatanın
çözümüdür:

- [ ] **`permissions:` bloğunda `id-token: write`** — action, GitHub App
      token'ını OIDC ile alır; yoksa
      `Unable to get ACTIONS_ID_TOKEN_REQUEST_URL` hatasıyla düşer.
- [ ] **Claude adımının `env:`'inde `GH_REPO: ${{ github.repository }}`** —
      yoksa agent'ın `gh` komutları repo bağlamı arar, tanı komutları izin
      reddine takılır ve turn'ler sessizce yanar (`error_max_turns`).
- [ ] **Checkout'tan ÖNCE koşan her `gh` adımında da `GH_REPO`** — yoksa
      `fatal: not a git repository` (Implementer'ın ilk label adımı böyle
      düşmüştü).
- [ ] **Reviewer/Triage'da `allowed_bots: "claude"`** — Implementer PR'ı
      `claude[bot]` olarak açar; bu input olmadan action
      "Workflow initiated by non-human actor" ile reddeder.
- [ ] **Comment yazan agent'lara (`reviewer/planner/triage`) `Write` izni**
      ve prompt'ta "gövdeyi `/tmp/<ad>.md`'ye Write ile yaz,
      `--body-file` ile gönder" talimatı — uzun comment'i Bash'e gömme
      girişimleri izin reddi + turn israfı üretir. (`contents: read`
      olduğundan Write push riski taşımaz. Bash `>` yönlendirmesi /tmp'ye
      engellidir; Write aracı serbesttir.)
- [ ] **Prompt'larda "Bash komutlarını tek tek çalıştır" kuralı** —
      `&&`, `;`, pipe, `>` içeren bileşik komutlar izin sistemine takılır.
- [ ] **Label geçişleri agent'ta değil workflow step'lerinde** ve
      **artefakt-tabanlı**: son comment'in ilk satırı `## Agent Plan` ise
      plan-ready, `## Agent Blocked` ise blocked — sürecin exit code'una
      bakmayın. (Planner geçerli planı yazıp max-turns'e takılınca exit
      code'a bakan mantık planı "blocked" saymıştı.)
- [ ] **`concurrency` grubu + `timeout-minutes` + `--max-turns`** her
      workflow'da (öneri: reviewer 25 / planner 30 / triage 20 /
      implementer 40 turn; 10-30 dk timeout).
- [ ] **Transcript artifact'ı**: `steps.claude.outputs.execution_file`
      varsa `actions/upload-artifact` ile 30 gün sakla — "agent neden
      böyle yaptı" sorusunun tek cevabı budur.
- [ ] **Label event guard'ı**: `if: github.event.label.name == '...'` —
      yoksa her label event'inde agent koşar.

## 6. Kurulum doğrulaması (smoke test sırası)

Fazları sırayla, her biri yeşilene kadar test edin:

1. **CI**: main'e push → `ci` yeşil; main'e direct push → GH006 reddi.
2. **Reviewer**: küçük, kasıtlı kusurlu bir test PR'ı açın (ör. testsiz
   bir endpoint) → önem-sıralı review comment'i gelmeli. Aynı PR'a iki
   push üst üste → ilk koşu `cancelled` olmalı (concurrency).
3. **Planner**: net bir issue + `agent:needs-plan` → plan comment'i +
   `agent:plan-ready`. Alakasız bir label ekleyin → koşu `skipped` olmalı.
4. **Implementer**: plana `agent:plan-approved` → testleri geçen PR +
   `agent:needs-review`; **PR'ın CI ve Reviewer'ı kendiliğinden
   tetiklediğini doğrulayın** (PAT testinin kanıtı budur).
5. **Triage**: lint'i geçip testi kıran bir PR açın → CI kırmızı →
   triage'ın kök neden comment'i PR'a düşmeli.

## 7. Günlük kullanım (özet)

```
issue aç + agent:needs-plan  →  plan gelir (plan-ready)
planı beğen + agent:plan-approved  →  PR gelir (needs-review)
review'u oku  →  merge et (issue kapanır)
CI kırmızıysa  →  triage'ın analizini oku
agent:blocked görürsen  →  comment'i oku, düzelt, giriş label'ını tekrar ekle
```

Kurallar: label'lara elle dokunmayın (blocked kurtarması hariç); issue'ları
küçük ve net yazın ("kapsam dışı" bölümü ekleyin); her agent koşusu
~$0.30'dur.

---

## 8. Sorun giderme tablosu (yaşanmış hataların tamamı)

| Belirti | Kök neden | Çözüm |
|---|---|---|
| `Unable to get ACTIONS_ID_TOKEN_REQUEST_URL` | `id-token: write` izni yok | `permissions:` bloğuna ekle |
| Koşu "success" ama agent hiçbir şey yapmadı; log'da "Skipping action due to workflow validation" | Workflow dosyası PR'da değiştirilmiş; action default branch'tekiyle aynı olmayan dosyayı çalıştırmaz | Workflow değişikliğini önce main'e merge et, sonra test et |
| `error_max_turns` + çok sayıda "permission denial"; comment atılamadı | Agent uzun comment'i dosyaya/Bash'e yazmaya çalıştı (Write izni yok) veya bileşik/tanı komutları reddedildi | `Write` iznini ver + `--body-file` akışı; prompt'a "komutları tek tek çalıştır"; `GH_REPO` env'i |
| `failed to run git: fatal: not a git repository` (workflow step'inde) | Checkout'tan önce `gh` çağrısı; repo bağlamı yok | Step env'ine `GH_REPO: ${{ github.repository }}` |
| `Workflow initiated by non-human actor: claude (type: Bot)` | Bot'un açtığı PR'ın tetiklediği koşuyu action reddediyor | `allowed_bots: "claude"` input'u |
| Implementer PR açtı ama Reviewer/CI hiç koşmadı | PR `github.token` ile açıldı; GitHub recursion koruması event'i bastırır | `AGENT_GITHUB_PAT` secret'ı (checkout `token:` + claude adımı `GH_TOKEN`) |
| Agent auth hatası / `ANTHROPIC_API_KEY` boş | Abonelikte `/install-github-app` farklı secret oluşturur | `claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}` input'unu da geçir |
| `gh secret set`: "accepts at most 1 arg(s), received 2" | Secret değeri pozisyonel argüman verilmiş | `--body "<değer>"` kullan; açığa çıkan token'ı rotate et |
| Kendi PR'ın merge edilemiyor (approval bekliyor) | Yazar kendi PR'ını approve edemez; `enforce_admins` bypass'ı kapatır | `required_approving_review_count: 0` (bkz. §3) |
| `Auto merge is not allowed for this repository` | Repo ayarı kapalı | `gh api -X PATCH repos/<o>/<r> -F allow_auto_merge=true` |
| Geçerli plan yazıldı ama issue `agent:blocked` oldu | Label geçişi exit code'a bakıyordu; koşu max-turns'e takıldı | Artefakt-tabanlı geçiş (son comment `## Agent Plan` mı?) |
| Auto-merge'e rağmen PR "open" kaldı | `strict` status check: branch main'in gerisinde | `gh api -X PUT repos/<o>/<r>/pulls/<n>/update-branch` |
| Push'ta HTTP 503 | GitHub geçici arızası | Bekle, tekrar dene |
| Lokal `pytest`: `unsupported operand type(s) for \|` | Python < 3.10 (`str \| None`) | Python 3.12 kullan veya doğrulamayı CI'a bırak |
| İki reviewer koşusu üst üste, eskisi çalışmaya devam ediyor | `concurrency` grubu yok | `concurrency.group` + `cancel-in-progress: true` |

## 9. Güvenlik notları

- PAT'i asla komut satırına pozisyonel yazmayın; sızarsa rotate edin.
- Agent'ların yazma yetkisi asgaridir: yalnızca Implementer `contents: write`
  taşır; reviewer/planner/triage comment'ten fazlasını yapamaz.
- `main` her zaman korumalıdır; en kötü senaryoda hasar bir branch'le
  sınırlıdır — branch'i silin, bitti.
- Secret expiry takibi `RUNBOOK.md`'deki tabloda yapılır.
