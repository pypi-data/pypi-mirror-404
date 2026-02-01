# {PROJECT_NAME} SaaS PRD (Pro)

> AI가 완벽히 이해하는 스펙. 정량적 기준, 에러 케이스, 테스트 시나리오 포함.
>
> 작성일: {DATE}
> 버전: 1.0
> 상태: Draft / Approved

---

## 1. 한 줄 정의

> **[타겟 사용자]**를 위한 **[핵심 가치]** SaaS - **[차별점]**

예시: "1인 창업자를 위한 랜딩 페이지 빌더 SaaS - 코드 없이 10분 만에 런칭"

---

## 2. 문제 정의

### 2.1 현재 문제

| 문제 | 심각도 | 빈도 | 현재 해결책 | 문제점 |
|------|--------|------|-------------|--------|
| [문제 1] | 높음 | 매일 | [기존 해결책] | [왜 불충분한가] |
| [문제 2] | 중간 | 주 1회 | | |

### 2.2 우리의 해결책

**Before**: [현재 사용자 경험]
**After**: [우리 제품 사용 후 경험]
**차이**: [정량적 개선 - 예: 4시간 → 10분]

---

## 3. 타겟 사용자

### 3.1 Primary 사용자
- **누구**: [예: 1인 창업자, 사이드 프로젝트 운영자]
- **규모**: [예: 월 100-1000 방문자 수준]
- **기술 수준**: [예: 비개발자, 노코드 도구 사용 경험 있음]
- **예산**: [예: 월 $10-50 지출 가능]

### 3.2 페르소나

**이름**: 김창업 (32세)
**직업**: 스타트업 대표 / 사이드 프로젝트 운영
**Pain Points**:
1. 개발자 고용 비용이 부담됨
2. 노코드 도구는 디자인이 별로
3. 빠르게 테스트하고 싶은데 시간이 오래 걸림

**Goals**:
1. 아이디어를 1주일 내 MVP로 검증
2. 코드 없이 전문적인 결과물

**Aha Moment**: [사용자가 "이거다!" 하는 순간]
예: "첫 프로젝트 생성 후 실제 동작하는 URL을 받았을 때"

---

## 4. 핵심 기능 상세

### 4.1 P0: 회원가입/로그인

#### Input/Output Specification

| 항목 | 상세 |
|------|------|
| **Input** | email (RFC 5322), password (8-128자, 대소문자+숫자+특수문자) |
| **Output (성공)** | JWT 토큰 (15분 만료) + Refresh 토큰 (7일) |
| **Output (실패)** | 에러 코드 + 사용자 친화적 메시지 |

#### Error Cases

| 코드 | 상황 | 응답 | 사용자 메시지 |
|------|------|------|--------------|
| 400 | 이메일 형식 오류 | `{"error": "invalid_email"}` | "올바른 이메일을 입력해주세요" |
| 400 | 비밀번호 규칙 불충족 | `{"error": "weak_password"}` | "비밀번호는 8자 이상, 대소문자+숫자+특수문자 포함" |
| 401 | 잘못된 자격증명 | `{"error": "invalid_credentials"}` | "이메일 또는 비밀번호가 일치하지 않습니다" |
| 409 | 이미 존재하는 이메일 | `{"error": "email_exists"}` | "이미 가입된 이메일입니다" |
| 429 | Rate limit (5회/분) | `{"error": "too_many_requests"}` | "잠시 후 다시 시도해주세요" |
| 423 | 계정 잠금 (10회 실패) | `{"error": "account_locked"}` | "계정이 잠겼습니다. 30분 후 다시 시도하거나 비밀번호를 재설정하세요" |

#### Test Scenarios

- [ ] 정상 회원가입 → 200 + 이메일 인증 메일 발송
- [ ] 정상 로그인 → 200 + JWT 반환
- [ ] 잘못된 비밀번호 → 401 (구체적 이유 노출 금지)
- [ ] 10회 실패 → 423 + 30분 잠금
- [ ] 잠금 후 30분 경과 → 재시도 가능
- [ ] 소셜 로그인 (Google) → OAuth 플로우 완료

---

### 4.2 P0: 결제 연동

#### State Machine

```
[Guest] --가입--> [Free]
              |
              |--업그레이드--> [Checkout]
              |                    |
              |                    |--성공--> [Pro Active]
              |                    |--실패--> [Free] + 에러 표시
              |                    |--취소--> [Free]
              |
[Pro Active] --결제 실패--> [Pro Grace Period (7일)]
                                |
                                |--결제 성공--> [Pro Active]
                                |--7일 경과--> [Pro Expired] --자동--> [Free]

[Pro Active] --취소 요청--> [Pro Canceling] --기간 종료--> [Free]
```

#### Input/Output Specification

| 항목 | 상세 |
|------|------|
| **Checkout Input** | plan_id, success_url, cancel_url |
| **Checkout Output** | Stripe Checkout Session URL |
| **Webhook Input** | Stripe Event (signature 필수 검증) |
| **Webhook Output** | 200 OK (처리 완료) 또는 4xx/5xx (재시도 필요) |

#### Error Cases

| 상황 | 처리 | 사용자 액션 |
|------|------|------------|
| 카드 거절 | Stripe 에러 메시지 표시 | 다른 카드 입력 |
| Webhook 서명 불일치 | 요청 거부 + 로깅 | (내부 처리) |
| 중복 결제 시도 | 기존 구독 확인 후 안내 | 빌링 포털로 이동 |
| 결제 실패 (잔액 부족) | 1차: 즉시 알림, 2차: +3일, 3차: +7일 다운그레이드 | 결제 수단 업데이트 |

#### Test Scenarios

- [ ] Free → Pro 업그레이드 → 결제 성공 → Pro 활성화
- [ ] 결제 중 취소 → Free 유지
- [ ] 카드 거절 → 에러 메시지 + 재시도 가능
- [ ] Pro → 취소 → 기간 종료까지 Pro 유지 → Free 전환
- [ ] 결제 실패 → 7일 Grace Period → 다운그레이드
- [ ] Webhook 서명 불일치 → 요청 거부 (400)

---

### 4.3 P0: [핵심 기능 1]

#### Input/Output Specification

| 항목 | 상세 |
|------|------|
| **Input** | [필드명]: [타입] ([검증 규칙]) |
| **Output (성공)** | [응답 구조] |
| **Output (실패)** | [에러 응답 구조] |

#### Error Cases

| 코드 | 상황 | 응답 |
|------|------|------|
| 400 | [입력 오류] | |
| 403 | [권한 없음] | |
| 404 | [리소스 없음] | |
| 422 | [비즈니스 로직 오류] | |

#### Test Scenarios

- [ ] 정상 케이스
- [ ] 빈 입력
- [ ] 최대 길이 초과
- [ ] 권한 없는 사용자 접근
- [ ] 존재하지 않는 리소스 접근

---

### 4.4 P1: [추가 기능들]

| 기능 | 설명 | Input | Output | 완료 조건 |
|------|------|-------|--------|-----------|
| 설정 페이지 | 프로필 수정 | name, avatar | 업데이트된 프로필 | 저장 후 반영 |
| 빌링 포털 | 구독 관리 | - | Stripe Portal URL | 포털 진입 |

---

## 5. Constraints (AI 경계)

### ALWAYS (무조건 실행)

- [ ] 모든 사용자 입력 서버에서 검증 (클라이언트 검증만 의존 금지)
- [ ] 결제 관련 모든 트랜잭션 로깅 (금액, 시간, 결과)
- [ ] Webhook 서명 검증 필수 (Stripe-Signature 헤더)
- [ ] 에러 발생 시 사용자 친화적 메시지 (스택 트레이스 노출 금지)
- [ ] 민감 데이터 암호화 저장 (bcrypt cost factor 12 이상)
- [ ] Rate Limiting 적용 (인증: 5회/분, API: 100회/분)

### ASK FIRST (확인 후 실행)

- [ ] 가격/플랜 변경
- [ ] DB 스키마 변경 (마이그레이션 필요)
- [ ] 결제 로직 수정
- [ ] 이메일 템플릿 변경
- [ ] 외부 API 연동 추가

### NEVER (절대 금지)

- [ ] **스펙에 없는 기능 구현** ← 가장 중요
- [ ] 하드코딩된 API 키/시크릿 (환경 변수 사용)
- [ ] 결제 금액 클라이언트에서 결정 (서버에서만)
- [ ] Webhook 서명 검증 생략
- [ ] 사용자 비밀번호 평문 저장/로깅
- [ ] 테스트 없이 결제 코드 배포
- [ ] 에러 메시지에 시스템 정보 노출
- [ ] 인증 없이 민감 API 노출

### Out of Scope (이번 버전에서 안 함)

| 기능 | 이유 | 예정 |
|------|------|------|
| 팀/멀티테넌트 | MVP 범위 초과 | v2.0 |
| 모바일 앱 | 웹 우선 | 미정 |
| 다국어 (영/한 외) | 리소스 부족 | 수요 시 |
| API 제공 | 요청 없음 | 수요 시 |
| SSO/SAML | 엔터프라이즈 기능 | Team 플랜 |

---

## 6. 가격 구조

### 6.1 플랜 정의

| 플랜 | 가격 | 제한 | 타겟 | 전환 트리거 |
|------|------|------|------|------------|
| Free | $0 | [예: 3개 프로젝트] | 체험 | - |
| Pro | $XX/월 | 무제한 | 개인 | 제한 도달 시 |
| Team | $XX/user/월 | 무제한 + 협업 | 팀 | 2명 이상 필요 시 |

### 6.2 결제 플로우

```
[랜딩] → [가입] → [Free 시작]
                      ↓
            [핵심 기능 사용]
                      ↓
            [제한 도달] ← 전환 트리거
                      ↓
         [업그레이드 CTA 표시]
                      ↓
         [Stripe Checkout]
                      ↓
    [성공] → [Webhook] → [DB 업데이트] → [Pro 활성화]
```

### 6.3 결제 실패 처리

| 단계 | 시점 | 액션 | 이메일 제목 |
|------|------|------|------------|
| 1차 알림 | 즉시 | 이메일 + 인앱 배너 | "결제 실패 - 결제 수단을 확인해주세요" |
| 2차 알림 | +3일 | 이메일 + 기능 제한 경고 | "3일 내 결제되지 않으면 Free로 전환됩니다" |
| 다운그레이드 | +7일 | Free 전환 + 이메일 | "Pro 구독이 종료되었습니다" |

### 6.4 환불 정책

- 첫 결제 후 7일 이내: 전액 환불
- 그 이후: 일할 계산 없음 (기간 종료까지 사용)
- 환불 시 즉시 Free 전환

---

## 7. SaaS 메트릭 목표

### 7.1 핵심 메트릭

| 메트릭 | 정의 | 목표 | 측정 방법 |
|--------|------|------|----------|
| **Activation Rate** | 가입 → 핵심 액션 완료 | > 40% | 가입 후 7일 내 [핵심 액션] 완료 |
| **D7 Retention** | 7일 후 재방문 | > 30% | 가입 후 7일차 로그인 |
| **Trial → Paid** | Free → Pro 전환 | > 5% | 가입 후 30일 내 결제 |
| **MRR** | 월 반복 매출 | 트래킹 | Stripe 대시보드 |
| **Churn Rate** | 월 이탈률 | < 5% | 취소/만료 구독 수 |

### 7.2 Aha Moment 정의

**Aha Moment**: [사용자가 가치를 느끼는 순간]

예시:
- "첫 [핵심 결과물] 생성 완료"
- "[핵심 기능]으로 첫 성과 달성"

**목표 시간**: 가입 후 [X]분 이내

### 7.3 온보딩 최적화

| 단계 | 목표 시간 | 완료 조건 | 드롭오프 시 액션 |
|------|----------|----------|----------------|
| 1. 가입 | 30초 | 소셜 로그인 완료 | - |
| 2. 첫 프로젝트 | 60초 | 프로젝트 생성 | 24시간 후 이메일 |
| 3. Aha Moment | 2분 | [핵심 액션] 완료 | 인앱 가이드 |
| 4. 활성화 | 7일 | 3회 이상 로그인 | 3일차 이메일 |

---

## 8. 화면 구조

### 8.1 사이트맵

```
/                           # 랜딩 페이지
├── /login                  # 로그인
├── /signup                 # 회원가입
├── /pricing                # 가격표
├── /dashboard              # 대시보드 (인증 필요)
│   ├── /dashboard/[기능1]
│   ├── /dashboard/[기능2]
│   └── /dashboard/new      # 새로 만들기
├── /settings               # 설정
│   ├── /settings/profile   # 프로필
│   ├── /settings/billing   # 결제/구독
│   └── /settings/notifications  # 알림
├── /api/*                  # API 엔드포인트
├── /webhook/*              # Webhook 엔드포인트
└── /404                    # 에러 페이지
```

### 8.2 상태별 UI

| 화면 | 로딩 | 빈 상태 | 에러 | 성공 |
|------|------|---------|------|------|
| 대시보드 | 스켈레톤 UI | "시작하기" CTA + 가이드 | 재시도 버튼 | - |
| 상세 페이지 | 스피너 | - | 인라인 에러 | 토스트 |
| 설정 | 스피너 | - | 필드별 에러 | "저장됨" 표시 |
| 결제 | 전체 로딩 + 메시지 | - | 명확한 에러 + 재시도/지원 | 성공 페이지 |

### 8.3 반응형 브레이크포인트

| 브레이크포인트 | 너비 | 레이아웃 |
|---------------|------|----------|
| Mobile | < 640px | 단일 컬럼, 햄버거 메뉴 |
| Tablet | 640-1024px | 2컬럼 가능 |
| Desktop | > 1024px | 사이드바 + 콘텐츠 |

---

## 9. 기술 스택

### 9.1 프론트엔드

| 구분 | 선택 | 이유 | 대안 |
|------|------|------|------|
| 프레임워크 | Next.js 14 | App Router, SSR | Remix |
| 스타일링 | Tailwind CSS | 빠른 개발 | CSS Modules |
| 상태관리 | Zustand | 간단함, 작은 번들 | Jotai |
| 폼 | React Hook Form + Zod | 검증 통합 | Formik |
| UI 컴포넌트 | shadcn/ui | 커스터마이징 가능 | Radix |

### 9.2 백엔드

| 구분 | 선택 | 이유 | 대안 |
|------|------|------|------|
| 인증 | Supabase Auth | 소셜 로그인 쉬움 | Clerk, Auth.js |
| DB | Supabase (PostgreSQL) | RLS, 실시간 | PlanetScale |
| 결제 | Stripe | 글로벌 표준 | Paddle (세금 처리) |
| 이메일 | Resend | 개발자 친화적 | SendGrid |

### 9.3 인프라

| 구분 | 선택 | 이유 | 비용 |
|------|------|------|------|
| 호스팅 | Vercel | Next.js 최적화 | Hobby: $0, Pro: $20/월 |
| DB | Supabase | 서버리스 | Free: 500MB |
| 모니터링 | Sentry | 에러 추적 | Free: 5K 이벤트 |
| 분석 | Posthog | 프로덕트 분석 | Free: 1M 이벤트 |

---

## 10. 데이터 모델

### 10.1 ERD 개요

```
users 1──N subscriptions
users 1──N [핵심 엔티티]
[핵심 엔티티] 1──N [하위 엔티티]
```

### 10.2 테이블 정의

#### users
| 컬럼 | 타입 | 설명 | 제약 | 인덱스 |
|------|------|------|------|--------|
| id | uuid | PK | NOT NULL, DEFAULT uuid_generate_v4() | PK |
| email | varchar(255) | 이메일 | UNIQUE, NOT NULL | UNIQUE |
| name | varchar(100) | 이름 | NOT NULL | |
| avatar_url | varchar(500) | 프로필 이미지 | | |
| plan | varchar(20) | 현재 플랜 | DEFAULT 'free' | |
| created_at | timestamptz | 생성일 | DEFAULT now() | |
| updated_at | timestamptz | 수정일 | DEFAULT now() | |

#### subscriptions
| 컬럼 | 타입 | 설명 | 제약 | 인덱스 |
|------|------|------|------|--------|
| id | uuid | PK | NOT NULL | PK |
| user_id | uuid | FK → users | NOT NULL | FK |
| stripe_customer_id | varchar(255) | Stripe 고객 ID | | |
| stripe_subscription_id | varchar(255) | Stripe 구독 ID | | UNIQUE |
| plan | varchar(20) | free/pro/team | NOT NULL | |
| status | varchar(20) | active/canceled/past_due/trialing | NOT NULL | |
| current_period_start | timestamptz | 현재 기간 시작 | | |
| current_period_end | timestamptz | 현재 기간 종료 | | |
| cancel_at_period_end | boolean | 기간 종료 시 취소 | DEFAULT false | |
| created_at | timestamptz | 생성일 | DEFAULT now() | |

#### [핵심 엔티티]
| 컬럼 | 타입 | 설명 | 제약 | 인덱스 |
|------|------|------|------|--------|
| id | uuid | PK | NOT NULL | PK |
| user_id | uuid | FK → users | NOT NULL | FK |
| [필드들] | | | | |
| created_at | timestamptz | 생성일 | DEFAULT now() | |
| updated_at | timestamptz | 수정일 | DEFAULT now() | |

### 10.3 RLS (Row Level Security) 정책

```sql
-- users: 본인만 조회/수정
CREATE POLICY "Users can view own data" ON users
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
  FOR UPDATE USING (auth.uid() = id);

-- [핵심 엔티티]: 본인 것만
CREATE POLICY "[Entity] owner access" ON [entity]
  FOR ALL USING (auth.uid() = user_id);
```

---

## 11. API 설계

### 11.1 인증 엔드포인트

| Method | Endpoint | 설명 | 인증 | Rate Limit |
|--------|----------|------|------|------------|
| POST | /auth/signup | 회원가입 | 불필요 | 5/분 |
| POST | /auth/login | 로그인 | 불필요 | 5/분 |
| POST | /auth/logout | 로그아웃 | 필요 | - |
| POST | /auth/refresh | 토큰 갱신 | Refresh 토큰 | 10/분 |
| POST | /auth/forgot-password | 비밀번호 찾기 | 불필요 | 3/시간 |
| POST | /auth/reset-password | 비밀번호 재설정 | 토큰 | 3/시간 |
| GET | /auth/me | 현재 사용자 | 필요 | - |

### 11.2 결제 엔드포인트

| Method | Endpoint | 설명 | 인증 | 특이사항 |
|--------|----------|------|------|----------|
| POST | /api/checkout | Checkout 세션 생성 | 필요 | plan_id 필수 |
| POST | /api/portal | 빌링 포털 URL | 필요 | 구독자만 |
| POST | /webhook/stripe | Stripe Webhook | Stripe 서명 | 서명 검증 필수 |

### 11.3 핵심 기능 엔드포인트

| Method | Endpoint | 설명 | 인증 | 응답 |
|--------|----------|------|------|------|
| GET | /api/[리소스] | 목록 조회 | 필요 | 페이지네이션 |
| GET | /api/[리소스]/:id | 상세 조회 | 필요 | 단일 객체 |
| POST | /api/[리소스] | 생성 | 필요 | 생성된 객체 |
| PUT | /api/[리소스]/:id | 수정 | 필요 | 수정된 객체 |
| DELETE | /api/[리소스]/:id | 삭제 | 필요 | 204 No Content |

### 11.4 공통 응답 형식

```json
// 성공
{
  "data": { ... },
  "meta": { "page": 1, "total": 100 }
}

// 에러
{
  "error": {
    "code": "invalid_input",
    "message": "사용자 친화적 메시지",
    "details": { "field": "email", "reason": "형식 오류" }
  }
}
```

---

## 12. 결제 체크리스트

### 12.1 Stripe 연동

- [ ] Stripe 계정 생성 + API 키 설정
- [ ] 환경 변수 설정 (STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET)
- [ ] Products/Prices 생성 (테스트 + 프로덕션)
- [ ] Checkout 세션 생성 로직 구현
- [ ] success_url, cancel_url 설정
- [ ] Webhook 엔드포인트 구현 (/webhook/stripe)
- [ ] Webhook 서명 검증 (stripe.webhooks.constructEvent)
- [ ] 이벤트 핸들러 구현:
  - [ ] checkout.session.completed
  - [ ] invoice.paid
  - [ ] invoice.payment_failed
  - [ ] customer.subscription.updated
  - [ ] customer.subscription.deleted
- [ ] Customer Portal 연동
- [ ] 테스트 모드에서 전체 플로우 테스트
- [ ] 프로덕션 Webhook 등록

### 12.2 결제 실패 처리

- [ ] invoice.payment_failed 핸들링
- [ ] 이메일 알림 발송 (1차: 즉시, 2차: +3일)
- [ ] 인앱 배너 표시
- [ ] Grace period (7일) 구현
- [ ] 자동 다운그레이드 로직
- [ ] 데이터 보존 정책 (다운그레이드 시 데이터 유지)

### 12.3 테스트 케이스

- [ ] 신규 구독 성공 (4242424242424242)
- [ ] 카드 거절 (4000000000000002)
- [ ] 결제 실패 후 재시도 성공
- [ ] 구독 취소 → 기간 종료 후 다운그레이드
- [ ] Webhook 서명 불일치 → 거부
- [ ] 중복 Webhook 처리 (멱등성)

---

## 13. 보안 체크리스트

### 13.1 인증/인가

- [ ] 비밀번호 해싱 (bcrypt, cost 12+)
- [ ] JWT 만료 시간 설정 (Access: 15분, Refresh: 7일)
- [ ] Refresh Token Rotation
- [ ] 세션 무효화 (로그아웃, 비밀번호 변경 시)
- [ ] Rate Limiting (로그인: 5/분, API: 100/분)

### 13.2 데이터 보호

- [ ] HTTPS 강제 (HSTS)
- [ ] 민감 데이터 암호화 저장
- [ ] SQL Injection 방지 (Prepared Statements)
- [ ] XSS 방지 (입력 이스케이프)
- [ ] CSRF 토큰

### 13.3 결제 보안

- [ ] Webhook 서명 검증
- [ ] 금액 서버에서만 결정
- [ ] PCI DSS 준수 (Stripe 사용으로 대부분 해결)
- [ ] 결제 로그 암호화 저장

---

## 14. 완료 정의 (Definition of Done)

### 14.1 기능별 DoD

| 기능 | 완료 조건 |
|------|----------|
| 회원가입 | 이메일/소셜 가입 동작 + 검증 이메일 발송 |
| 로그인 | JWT 발급 + Refresh 동작 + 10회 실패 잠금 |
| 결제 | Checkout → Webhook → Pro 활성화 전체 플로우 |
| 핵심 기능 | CRUD 동작 + 에러 핸들링 + 테스트 통과 |

### 14.2 품질 기준

- [ ] 테스트 커버리지 > 80%
- [ ] Lighthouse 성능 > 80점
- [ ] 에러 모니터링 (Sentry) 설정
- [ ] 프로덕트 분석 (Posthog) 설정
- [ ] 모든 P0 기능 동작 확인
- [ ] 결제 플로우 실제 테스트 (테스트 카드)

### 14.3 배포 전 체크리스트

- [ ] 환경 변수 프로덕션 값 설정
- [ ] Stripe 프로덕션 모드 전환
- [ ] Webhook 프로덕션 URL 등록
- [ ] 도메인 연결 + SSL 확인
- [ ] 에러 모니터링 알림 설정
- [ ] 백업 정책 확인

---

## 15. 마일스톤

| 단계 | 내용 | 완료 조건 | 예상 기간 |
|------|------|-----------|----------|
| M1 | 인증 + 기본 UI | 로그인/가입 동작, 대시보드 스켈레톤 | |
| M2 | 핵심 기능 | P0 기능 전체 동작 | |
| M3 | 결제 연동 | Stripe 결제 플로우 동작 | |
| M4 | 설정 + 빌링 | 구독 관리, 프로필 설정 | |
| M5 | 테스트 + QA | 테스트 커버리지 80%, 버그 수정 | |
| M6 | 배포 | 프로덕션 런칭 | |

---

## 변경 로그

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| {DATE} | 1.0 | 최초 작성 | |

---

## 부록: 용어 정의

| 용어 | 정의 |
|------|------|
| Aha Moment | 사용자가 제품 가치를 처음 느끼는 순간 |
| Activation | 가입 후 핵심 액션을 완료한 상태 |
| Grace Period | 결제 실패 후 서비스 유지 기간 |
| MRR | Monthly Recurring Revenue (월 반복 매출) |
| Churn | 구독 취소/이탈 |
