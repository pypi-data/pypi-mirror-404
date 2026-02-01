# {PROJECT_NAME} API PRD (Pro)

> AI가 완벽히 이해하는 API 스펙. 엔드포인트별 입출력, 에러 케이스, 테스트 시나리오 포함.
>
> 작성일: {DATE}
> 버전: 1.0
> 상태: Draft / Approved

---

## 1. 한 줄 정의

> **[클라이언트/서비스]**를 위한 **[핵심 기능]** REST API - **[차별점]**

예시: "SaaS 프론트엔드를 위한 사용자 인증 및 리소스 관리 API - 타입 안전성과 일관된 에러 처리"

---

## 2. API 개요

### 2.1 Base URL

| 환경 | URL | 비고 |
|------|-----|------|
| Production | `https://api.{PROJECT_NAME}.io/v1` | |
| Staging | `https://staging-api.{PROJECT_NAME}.io/v1` | |
| Local | `http://localhost:3000/v1` | |

### 2.2 버저닝 전략

```
URL 기반: /v1/users, /v2/users
헤더 기반: Accept: application/vnd.api+json;version=1 (미사용)
```

**버전 업 기준**:
- Breaking change (필드 삭제, 타입 변경) → Major 버전 증가
- 필드 추가, 기능 확장 → Minor 버전 (하위 호환)

### 2.3 콘텐츠 타입

```
요청: Content-Type: application/json
응답: Content-Type: application/json; charset=utf-8
```

---

## 3. 인증 (Authentication)

### 3.1 인증 방식

| 방식 | 용도 | 헤더 |
|------|------|------|
| Bearer Token | 일반 API 호출 | `Authorization: Bearer <access_token>` |
| API Key | 서버 간 통신 | `X-API-Key: <api_key>` |
| Webhook Signature | Webhook 검증 | `X-Signature: <hmac_sha256>` |

### 3.2 토큰 사양

| 토큰 | 형식 | 만료 | 갱신 방법 |
|------|------|------|----------|
| Access Token | JWT (RS256) | 15분 | Refresh Token으로 갱신 |
| Refresh Token | UUID v4 | 7일 | 재로그인 |
| API Key | 32자 hex | 없음 (수동 폐기) | 대시보드에서 재발급 |

### 3.3 JWT 페이로드

```json
{
  "sub": "user_uuid",
  "email": "user@example.com",
  "role": "user",
  "iat": 1234567890,
  "exp": 1234568790,
  "iss": "api.{PROJECT_NAME}.io"
}
```

### 3.4 인증 에러 응답

| 상황 | HTTP | 코드 | 응답 |
|------|------|------|------|
| 토큰 없음 | 401 | `AUTH_REQUIRED` | `{"error": {"code": "AUTH_REQUIRED", "message": "인증이 필요합니다"}}` |
| 토큰 만료 | 401 | `TOKEN_EXPIRED` | `{"error": {"code": "TOKEN_EXPIRED", "message": "토큰이 만료되었습니다"}}` |
| 토큰 무효 | 401 | `INVALID_TOKEN` | `{"error": {"code": "INVALID_TOKEN", "message": "유효하지 않은 토큰입니다"}}` |
| 권한 없음 | 403 | `FORBIDDEN` | `{"error": {"code": "FORBIDDEN", "message": "권한이 없습니다"}}` |

---

## 4. 공통 규격

### 4.1 요청 형식

```typescript
// 페이지네이션 쿼리
interface PaginationQuery {
  page?: number;      // 기본값: 1, 최소: 1
  limit?: number;     // 기본값: 20, 최대: 100
  sort?: string;      // 예: "created_at:desc"
}

// 필터링 쿼리
interface FilterQuery {
  [field: string]: string | number | boolean;  // 예: status=active
  q?: string;         // 전문 검색
}
```

### 4.2 응답 형식

```typescript
// 단일 리소스 응답
interface SingleResponse<T> {
  success: true;
  data: T;
}

// 목록 응답
interface ListResponse<T> {
  success: true;
  data: T[];
  meta: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
  };
}

// 에러 응답
interface ErrorResponse {
  success: false;
  error: {
    code: string;           // 기계 판독용
    message: string;        // 사용자 표시용
    field?: string;         // 검증 에러 시
    details?: object;       // 추가 정보
  };
}
```

### 4.3 공통 HTTP 상태 코드

| 코드 | 의미 | 사용 |
|------|------|------|
| 200 | OK | 조회, 수정 성공 |
| 201 | Created | 생성 성공 |
| 204 | No Content | 삭제 성공 |
| 400 | Bad Request | 입력 검증 실패 |
| 401 | Unauthorized | 인증 필요/실패 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 중복/충돌 |
| 422 | Unprocessable Entity | 비즈니스 로직 오류 |
| 429 | Too Many Requests | Rate Limit 초과 |
| 500 | Internal Server Error | 서버 오류 |

### 4.4 Rate Limiting

| 티어 | 제한 | 헤더 |
|------|------|------|
| Anonymous | 10 req/min | `X-RateLimit-*` |
| Free | 100 req/min | `X-RateLimit-*` |
| Pro | 1000 req/min | `X-RateLimit-*` |
| API Key | 10000 req/min | `X-RateLimit-*` |

**응답 헤더**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

**초과 시 응답**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "요청 한도를 초과했습니다",
    "details": {
      "retry_after": 60
    }
  }
}
```

---

## 5. 엔드포인트 상세

### 5.1 인증 API

#### POST /auth/signup

**설명**: 새 사용자 회원가입

**인증**: 불필요

**Rate Limit**: 10/시간/IP

**요청:**
```typescript
interface SignupRequest {
  email: string;      // RFC 5322, max 254자, unique
  password: string;   // 8-72자, 대문자+소문자+숫자 각 1개 이상
  name: string;       // 2-50자
}
```

```json
{
  "email": "user@example.com",
  "password": "SecurePass123",
  "name": "홍길동"
}
```

**응답 (201 Created):**
```typescript
interface SignupResponse {
  success: true;
  data: {
    user: {
      id: string;           // UUID v4
      email: string;
      name: string;
      email_verified: boolean;
      created_at: string;   // ISO 8601
    };
    message: string;
  };
}
```

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "홍길동",
      "email_verified": false,
      "created_at": "2026-02-01T00:00:00Z"
    },
    "message": "가입 완료. 이메일 인증을 진행해주세요."
  }
}
```

**에러 케이스:**

| 상황 | HTTP | 코드 | 응답 |
|------|------|------|------|
| 이메일 형식 오류 | 400 | `INVALID_EMAIL` | `{"field": "email", "message": "올바른 이메일 형식이 아닙니다"}` |
| 비밀번호 규칙 미충족 | 400 | `WEAK_PASSWORD` | `{"field": "password", "message": "비밀번호는 8자 이상, 대소문자+숫자 포함"}` |
| 이름 길이 오류 | 400 | `INVALID_NAME` | `{"field": "name", "message": "이름은 2-50자여야 합니다"}` |
| 이메일 중복 | 409 | `EMAIL_EXISTS` | `{"message": "이미 가입된 이메일입니다"}` |
| Rate Limit | 429 | `RATE_LIMITED` | `{"retry_after": 3600}` |

**테스트 시나리오:**
- [ ] 유효한 입력 → 201 + 사용자 정보 + 이메일 발송
- [ ] 이메일 형식 오류 → 400 + INVALID_EMAIL
- [ ] 약한 비밀번호 → 400 + WEAK_PASSWORD
- [ ] 중복 이메일 → 409 + EMAIL_EXISTS
- [ ] 11번째 요청 → 429 + Rate Limit

---

#### POST /auth/login

**설명**: 사용자 로그인

**인증**: 불필요

**Rate Limit**: 5/분/IP

**요청:**
```typescript
interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;  // default: false
}
```

**응답 (200 OK):**
```typescript
interface LoginResponse {
  success: true;
  data: {
    access_token: string;   // JWT
    refresh_token: string;  // UUID v4
    token_type: "Bearer";
    expires_in: number;     // 초 단위 (900 = 15분)
    user: {
      id: string;
      email: string;
      name: string;
      role: string;
    };
  };
}
```

**에러 케이스:**

| 상황 | HTTP | 코드 | 응답 |
|------|------|------|------|
| 필수 필드 누락 | 400 | `MISSING_FIELD` | `{"field": "email"}` |
| 잘못된 자격증명 | 401 | `INVALID_CREDENTIALS` | `{"message": "이메일 또는 비밀번호가 일치하지 않습니다"}` |
| 이메일 미인증 | 403 | `EMAIL_NOT_VERIFIED` | `{"message": "이메일 인증을 완료해주세요"}` |
| 계정 잠금 | 423 | `ACCOUNT_LOCKED` | `{"unlock_at": "2026-02-01T00:30:00Z"}` |
| Rate Limit | 429 | `RATE_LIMITED` | `{"retry_after": 60}` |

**보안 규칙:**
- 10회 연속 실패 → 30분 계정 잠금
- 실패 메시지에 구체적 이유 노출 금지
- 모든 시도 로깅 (IP, User-Agent, 시간)

**테스트 시나리오:**
- [ ] 유효한 자격증명 → 200 + 토큰
- [ ] 잘못된 비밀번호 → 401 (구체적 이유 없이)
- [ ] 미인증 이메일 → 403
- [ ] 10회 실패 → 423 + 30분 잠금
- [ ] 잠금 중 정확한 비밀번호 → 여전히 423
- [ ] remember_me=true → refresh_token 30일

---

#### POST /auth/refresh

**설명**: Access Token 갱신

**인증**: Refresh Token (Body)

**Rate Limit**: 10/분/사용자

**요청:**
```typescript
interface RefreshRequest {
  refresh_token: string;
}
```

**응답 (200 OK):**
```typescript
interface RefreshResponse {
  success: true;
  data: {
    access_token: string;
    expires_in: number;
  };
}
```

**에러 케이스:**

| 상황 | HTTP | 코드 |
|------|------|------|
| 토큰 없음/만료 | 401 | `INVALID_REFRESH_TOKEN` |
| 토큰 사용됨 (재사용 공격) | 401 | `TOKEN_REUSED` |

**보안 규칙:**
- Refresh Token은 1회용 (Rotation)
- 재사용 감지 시 모든 세션 무효화

---

#### POST /auth/logout

**설명**: 로그아웃 (토큰 무효화)

**인증**: Bearer Token

**요청:**
```typescript
interface LogoutRequest {
  all_devices?: boolean;  // true면 모든 세션 로그아웃
}
```

**응답 (204 No Content)**: 본문 없음

---

### 5.2 리소스 CRUD API

#### GET /api/{resource}

**설명**: 리소스 목록 조회

**인증**: Bearer Token

**Rate Limit**: 100/분

**쿼리 파라미터:**
```typescript
interface ListQuery {
  page?: number;        // default: 1
  limit?: number;       // default: 20, max: 100
  sort?: string;        // "field:asc" or "field:desc"
  status?: string;      // 필터: active, archived
  q?: string;           // 검색어
  created_after?: string;   // ISO 8601
  created_before?: string;  // ISO 8601
}
```

**예시 요청:**
```
GET /api/projects?page=1&limit=10&sort=created_at:desc&status=active
```

**응답 (200 OK):**
```typescript
interface ResourceListResponse {
  success: true;
  data: Resource[];
  meta: {
    page: number;
    limit: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}
```

**에러 케이스:**

| 상황 | HTTP | 코드 |
|------|------|------|
| 인증 없음 | 401 | `AUTH_REQUIRED` |
| 잘못된 page/limit | 400 | `INVALID_PAGINATION` |
| 잘못된 sort 형식 | 400 | `INVALID_SORT` |

**캐싱:**
```
Cache-Control: private, max-age=60
ETag: "abc123"
```

---

#### GET /api/{resource}/:id

**설명**: 리소스 단건 조회

**인증**: Bearer Token

**응답 (200 OK):**
```typescript
interface ResourceResponse {
  success: true;
  data: Resource;
}
```

**에러 케이스:**

| 상황 | HTTP | 코드 |
|------|------|------|
| 리소스 없음 | 404 | `NOT_FOUND` |
| 타인 리소스 | 403 | `FORBIDDEN` |

---

#### POST /api/{resource}

**설명**: 리소스 생성

**인증**: Bearer Token

**Rate Limit**: 30/분

**요청:**
```typescript
interface CreateResourceRequest {
  name: string;         // 1-100자, 필수
  description?: string; // max 1000자
  status?: "active" | "draft";  // default: draft
  metadata?: Record<string, any>;  // max 10 keys
}
```

**응답 (201 Created):**
```typescript
interface CreateResourceResponse {
  success: true;
  data: Resource;
}
```

**헤더:**
```
Location: /api/{resource}/550e8400-e29b-41d4-a716-446655440000
```

**에러 케이스:**

| 상황 | HTTP | 코드 |
|------|------|------|
| 필수 필드 누락 | 400 | `MISSING_FIELD` |
| 이름 길이 초과 | 400 | `INVALID_NAME` |
| 중복 이름 | 409 | `DUPLICATE_NAME` |
| 쿼터 초과 (Free) | 403 | `QUOTA_EXCEEDED` |

**테스트 시나리오:**
- [ ] 유효한 입력 → 201 + Location 헤더
- [ ] name 누락 → 400 + MISSING_FIELD
- [ ] Free 티어 10개 초과 → 403 + QUOTA_EXCEEDED

---

#### PUT /api/{resource}/:id

**설명**: 리소스 전체 수정

**인증**: Bearer Token

**요청:**
```typescript
interface UpdateResourceRequest {
  name: string;
  description?: string;
  status?: "active" | "draft" | "archived";
  metadata?: Record<string, any>;
}
```

**응답 (200 OK):**
```typescript
interface UpdateResourceResponse {
  success: true;
  data: Resource;
}
```

**에러 케이스:**

| 상황 | HTTP | 코드 |
|------|------|------|
| 리소스 없음 | 404 | `NOT_FOUND` |
| 타인 리소스 | 403 | `FORBIDDEN` |
| 버전 충돌 | 409 | `VERSION_CONFLICT` |

**동시성 제어:**
```
요청 헤더: If-Match: "abc123"
응답 헤더: ETag: "def456"
```

---

#### PATCH /api/{resource}/:id

**설명**: 리소스 부분 수정

**인증**: Bearer Token

**요청:**
```typescript
interface PatchResourceRequest {
  name?: string;
  description?: string;
  status?: string;
  // 전달된 필드만 수정
}
```

---

#### DELETE /api/{resource}/:id

**설명**: 리소스 삭제

**인증**: Bearer Token

**응답 (204 No Content)**: 본문 없음

**에러 케이스:**

| 상황 | HTTP | 코드 |
|------|------|------|
| 리소스 없음 | 404 | `NOT_FOUND` |
| 타인 리소스 | 403 | `FORBIDDEN` |
| 삭제 불가 상태 | 422 | `CANNOT_DELETE` |

**Soft Delete:**
- 실제 삭제 대신 `deleted_at` 설정
- 30일 후 완전 삭제 (배치 작업)

---

### 5.3 Webhook API

#### POST /webhook/{provider}

**설명**: 외부 서비스 Webhook 수신

**인증**: 서명 검증

**서명 검증:**
```typescript
// Stripe 예시
const signature = request.headers['stripe-signature'];
const event = stripe.webhooks.constructEvent(
  request.body,
  signature,
  process.env.STRIPE_WEBHOOK_SECRET
);
```

**응답:**
- 성공: 200 OK (빠른 응답 필수, 5초 이내)
- 실패: 4xx/5xx (재시도 트리거)

**멱등성:**
- 이벤트 ID로 중복 처리 방지
- 같은 이벤트 재수신 시 200 OK (작업 skip)

**처리할 이벤트:**

| 이벤트 | 처리 |
|--------|------|
| `checkout.session.completed` | 구독 활성화 |
| `invoice.paid` | 결제 완료 기록 |
| `invoice.payment_failed` | 결제 실패 알림 |
| `customer.subscription.deleted` | 구독 취소 처리 |

---

## 6. 데이터 모델

### 6.1 ERD 개요

```
users 1──N sessions
users 1──N resources
users 1──N subscriptions
resources 1──N resource_versions
```

### 6.2 테이블 정의

#### users
| 컬럼 | 타입 | 설명 | 제약 | 인덱스 |
|------|------|------|------|--------|
| id | uuid | PK | NOT NULL, DEFAULT uuid_generate_v4() | PK |
| email | varchar(255) | 이메일 | UNIQUE, NOT NULL | UNIQUE |
| password_hash | varchar(255) | 비밀번호 해시 | NOT NULL | |
| name | varchar(100) | 이름 | NOT NULL | |
| role | varchar(20) | user/admin | DEFAULT 'user' | |
| email_verified_at | timestamptz | 이메일 인증일 | | |
| failed_login_attempts | int | 로그인 실패 횟수 | DEFAULT 0 | |
| locked_until | timestamptz | 잠금 해제 시간 | | |
| created_at | timestamptz | 생성일 | DEFAULT now() | |
| updated_at | timestamptz | 수정일 | DEFAULT now() | |

#### sessions
| 컬럼 | 타입 | 설명 | 제약 | 인덱스 |
|------|------|------|------|--------|
| id | uuid | PK | NOT NULL | PK |
| user_id | uuid | FK → users | NOT NULL | FK |
| refresh_token_hash | varchar(255) | Refresh 토큰 해시 | NOT NULL | UNIQUE |
| user_agent | varchar(500) | 브라우저 정보 | | |
| ip_address | inet | IP 주소 | | |
| expires_at | timestamptz | 만료일 | NOT NULL | |
| created_at | timestamptz | 생성일 | DEFAULT now() | |

#### resources
| 컬럼 | 타입 | 설명 | 제약 | 인덱스 |
|------|------|------|------|--------|
| id | uuid | PK | NOT NULL | PK |
| user_id | uuid | FK → users | NOT NULL | FK |
| name | varchar(100) | 이름 | NOT NULL | |
| description | text | 설명 | | |
| status | varchar(20) | draft/active/archived | DEFAULT 'draft' | |
| metadata | jsonb | 메타데이터 | DEFAULT '{}' | GIN |
| version | int | 버전 (동시성 제어) | DEFAULT 1 | |
| created_at | timestamptz | 생성일 | DEFAULT now() | |
| updated_at | timestamptz | 수정일 | DEFAULT now() | |
| deleted_at | timestamptz | 삭제일 (soft delete) | | |

### 6.3 인덱스 전략

```sql
-- 복합 인덱스
CREATE INDEX idx_resources_user_status ON resources(user_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_resources_user_created ON resources(user_id, created_at DESC) WHERE deleted_at IS NULL;

-- 전문 검색
CREATE INDEX idx_resources_search ON resources USING GIN(to_tsvector('simple', name || ' ' || COALESCE(description, '')));
```

---

## 7. Constraints (AI 경계)

### ALWAYS (무조건 실행)

- [ ] 모든 입력은 서버에서 검증 (Zod/Joi 사용)
- [ ] 모든 응답에 올바른 HTTP 상태 코드
- [ ] 모든 에러는 구조화된 형식으로 응답
- [ ] 모든 요청/응답 로깅 (민감 정보 마스킹)
- [ ] Rate Limiting 미들웨어 적용
- [ ] CORS 미들웨어 적용
- [ ] 보안 헤더 설정 (Helmet)

### ASK FIRST (확인 후 실행)

- [ ] 새 엔드포인트 추가
- [ ] DB 스키마 변경
- [ ] 인증 로직 수정
- [ ] Rate Limit 값 변경
- [ ] 새 의존성 추가

### NEVER (절대 금지)

- [ ] **스펙에 없는 엔드포인트 구현**
- [ ] 하드코딩된 시크릿/API 키
- [ ] SQL 직접 작성 (ORM/Query Builder 사용)
- [ ] 에러 catch 후 빈 응답 반환
- [ ] 사용자 입력 직접 쿼리 삽입
- [ ] 비밀번호/토큰 로깅
- [ ] 스택 트레이스 클라이언트 노출
- [ ] 동기 블로킹 작업 (무거운 작업은 큐 사용)

### Out of Scope (이번 버전에서 안 함)

| 기능 | 이유 | 추가 예정 |
|------|------|----------|
| GraphQL | REST로 충분 | 수요 시 |
| WebSocket | 실시간 불필요 | v2.0 |
| 파일 업로드 | MVP 범위 초과 | v1.5 |
| Batch API | 단일 요청으로 충분 | 수요 시 |

---

## 8. 기술 스택

### 8.1 런타임 & 프레임워크

| 구분 | 선택 | 버전 | 이유 |
|------|------|------|------|
| 런타임 | Node.js | 20 LTS | 안정성, 생태계 |
| 언어 | TypeScript | 5.3+ | 타입 안전성 |
| 프레임워크 | Express / Fastify | 4.x / 4.x | 성숙도 / 성능 |
| 검증 | Zod | 3.x | 타입 추론 |
| ORM | Prisma / Drizzle | 5.x / 0.29+ | 타입 안전성 |

### 8.2 인프라

| 구분 | 선택 | 이유 |
|------|------|------|
| DB | PostgreSQL 15+ | 안정성, 기능 |
| 캐시 | Redis | 세션, Rate Limit |
| 호스팅 | Railway / Render | 쉬운 배포 |
| 모니터링 | Sentry | 에러 추적 |
| 로깅 | Pino | 성능 |

### 8.3 문서화

| 구분 | 선택 |
|------|------|
| 스펙 | OpenAPI 3.1 |
| UI | Swagger UI / Scalar |
| 클라이언트 생성 | openapi-typescript |

---

## 9. 비기능 요구사항

### 9.1 성능

| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| API 응답 (p50) | < 50ms | APM |
| API 응답 (p95) | < 200ms | APM |
| API 응답 (p99) | < 500ms | APM |
| 처리량 | > 500 req/s | k6 |
| DB 쿼리 | < 10ms (p95) | Slow query log |

### 9.2 가용성

| 항목 | 목표 |
|------|------|
| Uptime | 99.9% (월 43분 다운타임) |
| 장애 감지 | < 1분 |
| 장애 복구 | < 5분 |

### 9.3 확장성

| 항목 | 현재 | 6개월 후 | 설계 기준 |
|------|------|----------|----------|
| 사용자 | 1,000 | 10,000 | 100,000 |
| 요청/초 | 50 | 500 | 5,000 |
| DB 크기 | 1GB | 10GB | 100GB |

---

## 10. 보안 체크리스트

### 10.1 인증/인가

- [ ] 비밀번호 해싱 (bcrypt, cost 12+)
- [ ] JWT RS256 서명
- [ ] Refresh Token Rotation
- [ ] 계정 잠금 (10회 실패)
- [ ] 세션 무효화 지원

### 10.2 입력 검증

- [ ] 모든 입력 스키마 검증
- [ ] SQL Injection 방지 (ORM)
- [ ] NoSQL Injection 방지
- [ ] XSS 방지 (출력 이스케이프)
- [ ] Path Traversal 방지

### 10.3 전송 보안

- [ ] HTTPS only (HSTS)
- [ ] Secure Cookie (httpOnly, sameSite)
- [ ] CORS 화이트리스트
- [ ] Rate Limiting

### 10.4 보안 헤더

```typescript
// Helmet 설정
helmet({
  contentSecurityPolicy: true,
  crossOriginEmbedderPolicy: true,
  crossOriginOpenerPolicy: true,
  crossOriginResourcePolicy: true,
  dnsPrefetchControl: true,
  frameguard: true,
  hidePoweredBy: true,
  hsts: true,
  ieNoOpen: true,
  noSniff: true,
  originAgentCluster: true,
  permittedCrossDomainPolicies: true,
  referrerPolicy: true,
  xssFilter: true,
});
```

---

## 11. 테스트 전략

### 11.1 테스트 종류

| 종류 | 커버리지 목표 | 도구 |
|------|-------------|------|
| Unit | 80% | Vitest |
| Integration | 주요 플로우 | Supertest |
| E2E | 핵심 시나리오 | Playwright |
| Load | 목표 처리량 | k6 |

### 11.2 테스트 데이터

```typescript
// 테스트 사용자
const testUser = {
  email: "test@example.com",
  password: "TestPass123!",
  name: "테스트 사용자"
};

// 테스트 토큰
const testToken = jwt.sign({ sub: "test-user-id" }, SECRET, { expiresIn: "1h" });
```

### 11.3 엔드포인트별 테스트 시나리오

모든 엔드포인트에 대해:
- [ ] Happy path
- [ ] 인증 없이 호출 → 401
- [ ] 권한 없이 호출 → 403
- [ ] 잘못된 입력 → 400
- [ ] 존재하지 않는 리소스 → 404
- [ ] Rate Limit 초과 → 429

---

## 12. 완료 정의 (DoD)

### 12.1 엔드포인트별 DoD

| 항목 | 조건 |
|------|------|
| 기능 | 스펙대로 동작 |
| 검증 | 입력 스키마 검증 |
| 에러 | 모든 에러 케이스 처리 |
| 테스트 | 커버리지 80% 이상 |
| 문서 | OpenAPI 스펙 작성 |
| 로깅 | 요청/응답/에러 로깅 |

### 12.2 전체 DoD

- [ ] 모든 P0 엔드포인트 동작
- [ ] OpenAPI 스펙 완성
- [ ] Swagger UI 접근 가능
- [ ] 테스트 커버리지 80%
- [ ] 부하 테스트 통과 (500 req/s)
- [ ] 보안 체크리스트 완료
- [ ] 프로덕션 배포 완료

---

## 13. 마일스톤

| 단계 | 내용 | 완료 조건 |
|------|------|-----------|
| M1 | 프로젝트 설정 | 기본 구조, 미들웨어, DB 연결 |
| M2 | 인증 API | signup, login, refresh, logout |
| M3 | 리소스 CRUD | 목록, 상세, 생성, 수정, 삭제 |
| M4 | Webhook | Stripe 연동 |
| M5 | 테스트 & 문서 | 커버리지 80%, OpenAPI |
| M6 | 배포 | 프로덕션 런칭 |

---

## 변경 로그

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| {DATE} | 1.0 | 최초 작성 | |

---

## 부록: OpenAPI 스펙 예시

```yaml
openapi: 3.1.0
info:
  title: {PROJECT_NAME} API
  version: 1.0.0
  description: {PROJECT_NAME} REST API

servers:
  - url: https://api.{PROJECT_NAME}.io/v1
    description: Production
  - url: http://localhost:3000/v1
    description: Local

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    Error:
      type: object
      properties:
        success:
          type: boolean
          example: false
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string

paths:
  /auth/login:
    post:
      summary: 로그인
      tags: [Auth]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  minLength: 8
      responses:
        '200':
          description: 로그인 성공
        '401':
          description: 인증 실패
```
