---
name: creative-amazon-a-plus-visual-plan
description: Turn a product image and brief into a production-ready Amazon A+ visual operating plan with image-by-image creative direction, layout guidance, and exportable JSON.
---

# Amazon A+ Visual Plan

This skill turns a product image plus business inputs into a structured A+ detail-page visual plan. It is designed for operational use, not copywriting fluff.

Use it when the user wants:
- an Amazon A+ image plan
- a product-photoshoot operating list
- image-by-image creative direction for e-commerce visuals
- a JSON output that can feed downstream image generation or design workflows

## What this skill does

It produces a deterministic plan with:
- category-aware narrative structure
- image count allocation
- per-image creative execution plans
- pure image-content direction
- post-production layout direction
- guardrails against false claims
- a self-check section describing likely failure points

## Inputs

Expect these fields when available:
- product image
- product core information: brand, function, audience, category
- theme color
- font style
- target sales country
- image copy language
- aspect ratio
- image count
- extra user notes

If some inputs are missing, infer only what is visible from the image and clearly label assumptions.
Do not invent certifications, performance claims, or usage scenarios that are not supported by the image or user brief.

## Core workflow

### 1) Identify the product category
Infer the closest category from the image and brief:
- Tech / 3C
- Home / Kitchen / Pets
- Fashion / Shoes / Bags
- Beauty / Personal Care
- Other

If the product does not fit a default bucket, define a custom narrative path based on the product's purchase logic.

### 2) Choose a narrative path
Map the category to the most useful visual story:
- Tech: hero, feature breakdown, lifestyle use, comparison/specs
- Home: hero, action, details, size/storage
- Fashion: vibe, fit, texture, guide
- Beauty: texture, ingredients, routine, trust
- Other: build a custom sequence that matches the buying decision

### 3) Allocate image roles
Assign each image a clear job.
Typical roles:
- hero
- feature
- lifestyle
- detail
- comparison
- guide
- trust

The ratio must sum cleanly to the provided image count.

### 4) Write each image plan
For each image, output two parts:
- `Image Content Design`: pure visual scene only, no text overlay description
- `Layout Design`: text, fonts, placement, UI elements, framing, labels, badges, grids, lines

Each image plan must be standalone. It must not rely on another image for understanding.

### 5) Keep the output deterministic
Use one concrete choice per field.
No options, no ranges, no vague wording, no filler examples.

## Output format

Return valid JSON only.
The top-level key must be:
`operating_list_product_photoshoot`

Required fields:
- `total_number_of_images`
- `allocation_ratio`
- `image_design_list`

Each item in `image_design_list` must include:
- `image_number`
- `creative_execution_plan`
  - `image_type`
  - `image_content_design`
  - `layout_design`

## Writing rules for the output

- Use exact positions, angles, lighting direction, background materials, and composition language.
- Make the head image the strongest attention hook.
- Preserve consistency in theme color and typography.
- Adapt the palette to the target country if that affects visual taste.
- Use the theme color as a guide, not a hard constraint, when contrast would suffer.
- Keep the composition premium, clean, and conversion-focused.
- Prefer magazine-like structure, cinematic light, and minimal clutter.
- Do not use false claims, medical claims, or unsupported performance promises.
- Do not mention reference images or comparison images.
- Do not say “maybe”, “for example”, “or”, “etc.” in final JSON fields.

## Self-check before finalizing

Before giving the final answer, inspect the plan for these failure modes:

1. **The plan is too generic**
   - Symptom: every image sounds like “premium, clean, stylish” with no concrete scene.
   - Fix: name the object, angle, material, light, and composition.

2. **The plan is overpromising**
   - Symptom: claims about certifications, efficacy, or results that the user did not provide.
   - Fix: remove unsupported claims and stick to visible or user-provided facts.

3. **The plan ignores the product category**
   - Symptom: a tech product is described like fashion, or a beauty product is treated like hardware.
   - Fix: re-map the narrative logic to the real buying behavior.

4. **The output is not actually JSON-safe**
   - Symptom: trailing commas, Markdown fences, commentary, or nested explanations outside the schema.
   - Fix: return JSON only.

5. **The layout and image content overlap too much**
   - Symptom: the visual scene description already contains typography instructions, or the layout section repeats the scene.
   - Fix: keep the two sections separate.

6. **The image count allocation is messy**
   - Symptom: the total number of images does not match the list.
   - Fix: reconcile counts before output.

## Recommended response style

Be concise, operational, and concrete.
If the user provides a product image and brief, produce the full JSON plan immediately.
If the brief is missing important fields, infer only what is safe and mark assumptions internally, not in the JSON.

## Example structure

```json
{
  "operating_list_product_photoshoot": {
    "total_number_of_images": "5",
    "allocation_ratio": "Hero 20%, Feature 20%, Lifestyle 20%, Detail 20%, Comparison 20%",
    "image_design_list": [
      {
        "image_number": 1,
        "creative_execution_plan": {
          "image_type": "Hero",
          "image_content_design": "...",
          "layout_design": "..."
        }
      }
    ]
  }
}
```

## When not to use

Do not use this skill for:
- general marketing copy
- storefront banner copy only
- non-product creative writing
- unrelated design-system tasks

## Final self-check output requirement

After generating the plan, include a short plain-language self-check note if the user explicitly asks for it.
The self-check must call out likely weak spots, especially:
- over-abstract scene direction
- unsupported claims
- awkward image count allocation
- unclear typography instructions
- mismatch between category and visual narrative
