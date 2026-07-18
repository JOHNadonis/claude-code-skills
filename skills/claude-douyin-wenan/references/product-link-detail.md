# Product Link Detail Retrieval

Use this workflow when the user provides a product URL or asks to open a product page before writing copy. Build the fact card internally. Do not expose research notes unless the user asks.

## Retrieval Workflow

1. Preserve the original URL, follow redirects, and record the final URL, platform, shop, product ID, and selected SKU when available.
2. Open JavaScript-dependent pages with an available rendered browser and wait for product content to appear.
3. Extract only target-product fields: exact title, brand, category, shop, product ID, SKU, specification, quantity, ingredients or material, usage, applicable audience, merchant-declared selling points, price, promotion, service terms, and visible product-image evidence.
4. Inspect JSON-LD, embedded page state, rendered DOM, and the page's own network requests when visible text is incomplete.
5. For Haohuo or Jinritemai pages, derive the current product-detail request from the rendered page. Do not hard-code an old endpoint. Treat error responses as retrieval failure, not empty product data.
6. Do not bypass login, CAPTCHA, anti-bot controls, or platform permissions. Use an authorized browser session when available; otherwise ask for a screenshot, copied title, or confirmed selling points.

## Identity and Source Checks

- Match product ID and SKU whenever possible.
- Do not mix recommended products, reviews, old variants, search snippets, or similar products into the target fact card.
- Prefer the matching product page and its own detail request.
- Treat price, stock, discounts, gifts, and service terms as dynamic.
- Treat merchant statements as merchant claims, not independent proof.
- Omit disputed or unconfirmed fields.

## Fact Grades

### A — Source-confirmed

Use low-risk facts supplied by the user or directly visible on the matching product page, selected SKU, product image, or detail request.

### B — Creative context

Use ordinary audience, scene, emotion, and category actions for creative framing. Do not present them as page facts, reviews, technical claims, or current promotions.

### C — Forbidden or unconfirmed

Do not write inferred efficacy, ingredient concentration, certification, sales volume, ranking, endorsement, guaranteed result, medical effect, review content, or precise promotion without reliable evidence.

## Internal Product Fact Card

Record:

- Product identity and short spoken name
- Brand category shop product ID and SKU
- Specification quantity ingredients or material
- Simple usage
- A-grade selling points and source
- B-grade scenes and emotions
- Dynamic price or promotion with retrieval time
- C-grade gaps conflicts and forbidden claims

## Framework Grounding

Product facts only fill existing slots in the four frameworks defined by `SKILL.md`. They must never create another structure.

1. Choose exactly one of pain, effect, value, or scene framework before selecting product details.
2. Choose at most one core selling point for each script.
3. Use the selected fact only in the framework's product value, usage, effect, or advantage slot.
4. Do not append ingredient explanations, fragrance pyramids, specification lists, research notes, or a second selling-point paragraph.
5. Do not use every extracted fact merely because it was retrieved. Unused facts should remain internal.
6. Prefer a short spoken product name. Treat marketing modifiers in the full commerce title as details, not as part of the name.
7. A generic category action such as washing, applying, spraying, or rinsing can fill a usage slot without quoting the page.
8. An emotional or life result can fill an effect slot when it follows naturally from the scene and does not claim unsupported product efficacy.
9. A physical product result must come from A-grade information.
10. Ingredient, concentration, technology, exact specification, price, promotion, and service terms should default to absent unless the user asks or the value framework genuinely requires them.
11. Keep explicit page-detail wording to a minority of the batch when the four frameworks remain complete without it. Do not repeat the same extracted detail in consecutive scripts.
12. Never turn a confirmed scent note into an unconfirmed claim about longevity, projection, or another person's detectable reaction.
13. Never invent usage duration, repurchase history, family feedback, visible results, reviews, or official proof.

## Failure Handling

- If retrieval fails but the user supplied usable facts, write only from those facts and mention the limitation in the final handoff.
- If the URL is the only input and reliable facts cannot be recovered, ask for a screenshot, full title, and confirmed selling points before writing.

