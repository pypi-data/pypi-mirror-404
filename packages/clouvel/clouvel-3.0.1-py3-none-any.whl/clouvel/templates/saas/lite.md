# {PROJECT_NAME} SaaS PRD (Lite)

> MVP용. 핵심만. 하지만 AI가 빠뜨리면 안 되는 건 다 있음.
>
> 작성일: {DATE}

---

## 1. 한 줄 요약

**[타겟]**을 위한 **[핵심 가치]** SaaS

---

## 2. 문제 → 해결

| 문제 | 해결 |
|------|------|
| [사용자가 겪는 문제] | [이 SaaS가 해결하는 방법] |

---

## 3. 핵심 기능 (P0만)

| 기능 | 설명 | 완료 조건 |
|------|------|-----------|
| 로그인 | 이메일 + 소셜 | OAuth 동작 |
| 결제 | Stripe 구독 | 결제 → 활성화 |
| 대시보드 | 핵심 기능 UI | 로그인 후 진입 |
| [기능 1] | | |
| [기능 2] | | |

---

## 4. Constraints (AI 경계)

### ALWAYS (무조건)
- [ ] 모든 입력 검증
- [ ] 결제 트랜잭션 로깅
- [ ] Webhook 서명 검증

### NEVER (절대 금지)
- [ ] **스펙에 없는 기능 구현**
- [ ] 하드코딩된 API 키
- [ ] 결제 금액 클라이언트에서 결정
- [ ] Webhook 서명 검증 생략

### Out of Scope (이번에 안 함)
- 팀 기능 - v2에서
- 모바일 앱 - 웹 우선

---

## 5. 가격

| 플랜 | 가격 | 제한 |
|------|------|------|
| Free | $0 | [제한] |
| Pro | $XX/월 | 무제한 |

---

## 6. 화면

```
/           → 랜딩
/login      → 로그인
/signup     → 회원가입
/pricing    → 가격표
/dashboard  → 대시보드 (핵심)
/settings   → 설정 + 빌링
```

---

## 7. 기술 스택

| 구분 | 선택 |
|------|------|
| FE | Next.js + Tailwind |
| 인증 | Supabase / Clerk |
| 결제 | Stripe |
| DB | Supabase / PlanetScale |

---

## 8. 데이터 모델

### users
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| email | varchar | 이메일 |
| plan | varchar | free/pro |

### subscriptions
| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | uuid | PK |
| user_id | uuid | FK |
| stripe_subscription_id | varchar | Stripe ID |
| status | varchar | active/canceled |

---

## 9. API

| Method | Path | 설명 |
|--------|------|------|
| POST | /auth/signup | 회원가입 |
| POST | /auth/login | 로그인 |
| POST | /api/checkout | 결제 세션 |
| POST | /webhook/stripe | Stripe Webhook |

---

## 10. 결제 체크리스트

- [ ] Stripe Products/Prices 생성
- [ ] Checkout 세션 구현
- [ ] Webhook 서명 검증
- [ ] invoice.paid 핸들링
- [ ] 테스트 결제 성공

---

## 11. 완료 체크리스트

- [ ] 로그인 동작
- [ ] 결제 플로우 동작
- [ ] 핵심 기능 동작
- [ ] Webhook 서명 검증
- [ ] 테스트 커버리지 > 80%

---

## 변경 로그

| 날짜 | 내용 |
|------|------|
| {DATE} | 최초 작성 |
