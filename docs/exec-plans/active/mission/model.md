# Mission Model Superseded

`missions` 테이블과 Mission ORM 모델은 제거되었다.

대체 모델:
- `offers`: `accepted_at`, `delivery_completed_at`, `receipt_confirmed_at`, `settled_at`, `disputed_at`, `refunded_at`
- `proposals`: `matched_at`, `delivery_reported_at`, `received_confirmed_at`, `settled_at`, `disputed_at`, `refunded_at`
- `proofs`: `proposal_id`, `offer_id`, `actor_id`, `proof_type`, `image_url`, `reason`, `created_at`
