# JurisNG Design System & Styleguide
**Theme:** *Nigerian Jurisprudence & Heritage Parchment*  
**Design Philosophy:** Authoritative, Editorial, Legal-First. Avoids generic AI SaaS zinc/indigo clichés in favor of warm gazette tones, Nigerian federal spruce green, and polished court brass.

---

## 🎨 1. Color System

### Light Mode — *Luminous Alabaster & Editorial Parchment*
| Token Name | Hex Code | Usage |
| :--- | :--- | :--- |
| **`bg-canvas`** | `#f8f7f4` | Primary canvas. Clean, luminous warm alabaster stationery tone (zero dusty yellow cast). |
| **`bg-surface`** | `#ffffff` | Primary cards, search boxes, modals. Crisp, pure white. |
| **`bg-subtle`** | `#f1ede6` | Sidebar, secondary surfaces, suggestion button hovers. |
| **`border-default`** | `#e4dfd5` | Razor-sharp, subtle neutral warm borders and dividers. |
| **`border-focused`** | `#0d533f` | Active inputs and focused interactive elements. |
| **`text-primary`** | `#1a1815` | Deep Obsidian ink for statutory titles and body copy. |
| **`text-secondary`** | `#655e51` | Warm charcoal for metadata, subtitles, and labels. |
| **`text-muted`** | `#938a7b` | Section numbers, hints, timestamps. |
| **`accent-emerald`** | `#0d533f` | Primary brand accent: Deep Nigerian Federal Spruce Green. |
| **`accent-emerald-light`**| `#e6f2ed` | Badge backgrounds, active nav pill highlights. |
| **`accent-brass`** | `#9c6d1d` | Secondary accent: Supreme Court Brass / Seal Gold. |
| **`accent-brass-light`** | `#fbf3e4` | Secondary tags, notice alerts, highlight markers. |

### Dark Mode — *Midnight Ink & Warm Obsidian*
| Token Name | Hex Code | Usage |
| :--- | :--- | :--- |
| **`bg-canvas-dark`** | `#0e1014` | Deep executive warm-charcoal obsidian canvas (zero blue/navy cast). |
| **`bg-surface-dark`** | `#181b22` | Elevated card surfaces, search panels, input containers. |
| **`bg-subtle-dark`** | `#13161c` | Sidebar and modal container outer frames. |
| **`bg-hover-dark`** | `#222630` | Hover states and interactive rows. |
| **`border-default-dark`**| `#262a34` | Clean, subtle graphite container borders. |
| **`text-primary-dark`** | `#f5f4f0` | Soft warm milk-white statutory body reading text. |
| **`text-secondary-dark`**| `#9ca3af` | Balanced graphite for subtitles, metadata, author citations. |
| **`accent-emerald-dark`** | `#10b981` | Bright Nigerian emerald for active states and indicators. |
| **`accent-brass-dark`** | `#fbbf24` | Polished brass for warnings and statutory tags. |

---

## ✍️ 2. Typography Hierarchy

| Role | Font Family | Weight | Purpose |
| :--- | :--- | :--- | :--- |
| **Display / Titles** | `Newsreader` / `Playfair Display` (Serif) | 600, 700 | Hero titles, Act names, Legal Ruling headings. |
| **Interface & Controls**| `Plus Jakarta Sans` / `Geist` (Sans) | 400, 500, 600 | Navigation, search inputs, buttons, pills. |
| **Statutory Text** | `Newsreader` (Editorial Serif) | 400, 500 | Full statutory section reader, legal body text. |
| **Citations & Numbers** | `JetBrains Mono` (Monospace) | 500 | `Section 54`, `Cap. L11`, `[Issue I]`, Act years. |

---

## 🏛️ 3. Component Design Rules

1. **No Neon / AI Glow Effects:** Use crisp 1px borders (`#e6e0d2` / `#242b36`) and warm, natural elevation shadows (`rgba(27, 24, 21, 0.04)`).
2. **Book-like Statutory Reading:** Section text is rendered in editorial serif with comfortable `line-height: 1.75` and max reading line width.
3. **Parchment Badges:**
   - Active / Verified: Warm Green (`bg-[#0d533f]/10 text-[#0d533f]`)
   - Gazette / Watcher: Warm Brass (`bg-[#9c6d1d]/10 text-[#9c6d1d]`)
4. **First-Time User Onboarding Modal:**
   - Unobtrusive, dignified modal requiring explicit consent under the *Legal Practitioners Act (Cap. L11)* and *Copyright Act 2022*.
   - Stores consent token in `localStorage('jurisng_terms_agreed_v1')`.

---

## 🏷️ 4. Practice Area Classifications

1. **Banking & Securities** (BOFIA, ISA, AMCON, NDIC, Secured Transactions)
2. **Corporate & Commercial** (CAMA 2020, Startup Act, FCCPA, Trade Marks, Patents)
3. **Labor & Employment** (Labour Act, Employees' Compensation, Trade Unions, Factories)
4. **Police & Criminal Justice** (ACJA 2015, Police Act 2020, Criminal Code, Penal Code)
5. **Taxation & Revenue** (CITA, PITA, VAT, Stamp Duties, Capital Gains)
6. **Maritime & Cabotage** (Admiralty, Cabotage, NIMASA, NPA, Marine Insurance)
7. **Judicature & Procedure** (Constitution 1999, Supreme Court, Court of Appeal, FHC, NICN)
8. **Regional Development** (NWDC, SEDC, SWDC, NCDC, NDDC)
