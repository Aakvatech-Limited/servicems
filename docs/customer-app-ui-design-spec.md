# ServiceMS Customer App — UI/UX Design Contract

Status: **Design direction / marketing-quality mockup reference, pending final Product Owner approval of detailed screens.** This is a requirement for **one complete Phase 4 delivery**, not a separate implementation phase.

## 1. Reference and implementation rule

The Product Owner's Aakvatech-branded **Customer App showcase mockup generated in the Phase 4 ChatGPT conversation on 9 November 2026** is the *visual direction*: premium light canvas, deep navy navigation, vivid red accent, carefully spaced rounded white cards, fine automotive photography, compact status chips, typography hierarchy, functional touch targets and distinct mobile/desktop information architecture.

**Important:** The generated PNG is in the conversation and is **not embedded in this repository** by this text file. Do **not** claim pixel-perfect matching against it without obtaining the PNG and reviewing each implemented screen side by side. The reference is a direction, **not** a license to hardcode fake vehicle data, Indian currency, Aakvatech branding, a static progress percentage, appointment slots, or unsupported functions.

Codex should request/receive the mock PNG as a visual input for screenshot comparison, while this Markdown is the implementation/acceptance contract.

## 2. Product branding: white-label by Company

- The **garage's authorized company administrator** controls presentation in **Frappe Desk > ServiceMS > Customer App Settings**, never in the customer-facing Customer App.
- One Customer App brand per Company, shared by all eligible **Service Workshop** records. No per-workshop colour/logo override.
- Existing `Customer App Settings` already exposes `app_name`, `logo`, `pwa_icon`, `primary_color`, `secondary_color`, `navbar_color`, `theme` (System/Light/Dark), `welcome_message`, contact information and company-level enablement.
- Use Aakvatech colours **as fallback/demo tokens only**: primary `#bc2230`, secondary `#0d1d38`, navbar `#0d1d38`; supporting blue `#4b68ae`, `#5695d0`, neutral `#aaaab9`. The live Customer App must render the *selected Company's* saved values.
- Use validated, centrally defined CSS custom properties/design tokens with semantic names (e.g. `--customer-primary`, `--customer-secondary`, `--customer-navbar`, `--customer-bg`, `--customer-surface`, `--customer-text`, `--customer-border`, `--customer-focus`). Derive hover/disabled/surface variants safely. No scattered literal Aakvatech colours in components.
- Light/dark modes must preserve configured brand intent **and** readable contrast. Validate colour input, provide safe fallbacks, accessible text contrast and keyboard focus indicators.
- The garage's logo/app name appears in the Customer App header and PWA presentation, while **mandatory product attribution** appears subtly in the app footer: **`Powered by Aakvatech - ServiceMS`**. Attribution is fixed by ServiceMS, not configurable/removable by garage admins, and must not replace the garage's primary branding. The entire attribution label should link to the **Product Owner-supplied destination URL (pending)**; **do not invent, guess or hardcode a placeholder URL**. Keep it readable and accessible in light/dark themes.
- Administrators should have a **live Frappe Desk branding preview** for mobile and desktop; changing branding should not require source edits. Only authorized company managers may change their Company's settings.
- Customer App disabled: no Customer App frontend/API/auth entrance accessible; brand data preserved. Standard Frappe login/ERPNext Portal and internal ServiceMS Desk/Field PWA stay untouched. Public branding bootstrap must not leak another Company's private data.

## 3. Information architecture (customer-only)

Dedicated accessible customer screens:
1. Dashboard — upcoming booking, active repair status, pending approval, vehicle summary, relevant notifications.
2. Bookings — view/request/cancel/reschedule (where authorized); company-enabled Service Workshop selection.
3. My Vehicles — list and vehicle-specific service journey.
4. My Repairs / Job Cards — **current and historical** records with customer-safe work and status information.
5. Quotations — **current and historical** quotations, detailed breakdown, secure approvals/rejections and audit history.
6. Invoices — **current and historical** invoices, payment status, PDF downloads and permitted receipts.
7. Service History — vehicle-based history of completed visits with links to Job Card, quotation, invoice and inspections; records do not disappear when workshop booking availability is disabled.
8. Inspections — finished Pre/Post inspection reports and authorized photos, sourced from Phase 3B backend.
9. Notifications — status changes and relevant customer alerts.
10. My Account — permitted profile/preferences and sign-out only, **no admin settings**.

### Mobile layout

- Responsive **320px+**. Top branded header with logo/app name, notifications and customer profile.
- Dashboard hero/greeting, an emphasized upcoming booking and active repair status, pending quotation, and easy-to-find quick-action tiles **Job Cards / Quotations / Invoices / History**.
- Persistent compact bottom navigation: **Home / Bookings / Vehicles / More**. **More** opens the remaining dedicated sections (My Repairs, Quotations, Invoices, History, Inspections, Notifications, My Account). On long screens, keep actionable elements reachable without covering content.
- Booking interaction: choose permitted workshop and authorized vehicle, preferred date and *supported* time availability. Do not invent appointment duration/slots or Bay availability beyond ServiceMS backend capability.
- Repair detail: visible status/progress based on real data, safe work description, permitted inspection summary/photos. Do not display fabricated percent complete unless a real supported progress metric exists.
- Quotation/invoice detail: neat itemized figures, correct company currency and taxes from ERPNext, approval only when authorized, PDF download only if authorized.
- Keep touch targets accessible, no horizontal overflow, support safe areas, portrait and landscape, real phones and tablets.

### Desktop/tablet layout

- A strong branded **left sidebar** with individual entries for Dashboard, Bookings, My Vehicles, My Repairs (Job Cards), Quotations, Invoices, Service History, Inspections, Notifications, My Account.
- Spacious dashboard: top KPI cards, active repairs, upcoming bookings, vehicles and recent activity. Contextual actions visible without drowning in controls.
- Adaptive multi-column layout on wider viewports; on tablet shrink/collapse sidebar as needed; on narrow screens switch to mobile navigation. Avoid nested scrollbars and overly large whitespace.
- Show consistent status semantics: e.g. pending/action-needed, in-progress, completed; colors never the *only* status indication.

## 4. Interaction and content quality

- Avoid a static brochure: implement working navigation, detailed screens, loading/empty/error states, success and error feedback, accessible dialogs, validation and helpful confirmation flows.
- Prefer real ERPNext/ServiceMS data to fake totals or demo-only content; empty states are preferable to hardcoded sample invoices/vehicles.
- Show only authorized company + customer + vehicle records. Never expose internal technician notes, supplier costs, insurer-only information or private photos.
- Existing historical Job Cards/quotes/invoices are first-class destinations, not hidden solely under a generic 'Documents' section.
- Support readable typography, consistency, restrained micro-interactions, useful whitespace and attractive yet performant imagery. No decorative elements that obscure important actions.
- Company-specific workshop booking switches affect **new booking availability only**; they never erase previously authorized history.
- Show a consistent, unobtrusive **`Powered by Aakvatech - ServiceMS`** footer link on Customer App screens and the entry/login view when the app is enabled, including mobile, tablet and desktop. Place it after main content / at the bottom of the page, never as a floating obstruction or primary call-to-action. Keep link destination configurable centrally in product code only once the Product Owner supplies the exact URL; until then show accessible attribution text without a dead or invented hyperlink.

## 5. Acceptance checks before design sign-off

- Compare responsive app screens side by side against the provided visual mockup (once attached). Preserve its design *quality and structure* while adapting to real data and white-label branding.
- Test at 320, 375, 390, 430, 768, 820/834, 1024 and 1366+ px, portrait and landscape, light/dark modes; verify no clipping, horizontal overflow, poor tap targets or confusing navigation.
- Set Company A primary/nav colours and logo to one scheme, Company B to a different scheme. Verify every customer page and PWA icon/theme uses the correct company without cross-company leakage.
- Verify brand values from Desk update presentation without code change; invalid/low-contrast colours fail safely or use readable fallbacks.
- Confirm no admin settings in Customer App. Confirm Job Cards, Quotations, Invoices and Service History are directly discoverable on both mobile and desktop, including *old records*.
- Confirm disable/re-enable company, disabled workshop, document downloads and multi-company authorization regressions.
- Verify the fixed **Powered by Aakvatech - ServiceMS** attribution is legible and consistently placed at mobile and desktop sizes, uses the exact supplied URL once provided, opens safely, and cannot be hidden or altered by company branding settings.
- Keep the PR Draft and the environment separate from Phase 3B; do not merge/deploy to production before Product Owner approval.

## 6. Codex handoff

Implement the **entire agreed Phase 4 scope in the existing** `feat/v16-customer-app` branch / Draft PR #69, using this design contract. Treat the conversation-generated mockup as the look-and-feel source once separately supplied as a PNG. Report which UI screens and CSS theme bindings were actually implemented, screenshots and test outcomes, and remaining blockers. Do not describe this Markdown alone as implemented UI.
