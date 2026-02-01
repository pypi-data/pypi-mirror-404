# {PROJECT_NAME} CLI PRD (Pro)

> AI가 완벽히 이해하는 CLI 스펙. 명령어별 입출력, 에러 처리, 인터랙티브 플로우 포함.
>
> 작성일: {DATE}
> 버전: 1.0
> 상태: Draft / Approved

---

## 1. 한 줄 정의

> **[타겟 사용자]**를 위한 **[핵심 기능]** CLI 도구 - **[차별점]**

예시: "바이브코더를 위한 PRD 강제 도구 - 문서 없이 코딩 시작 차단"

---

## 2. CLI 개요

### 2.1 기본 정보

| 항목 | 값 |
|------|-----|
| 이름 | `{PROJECT_NAME}` |
| 별칭 | `{ALIAS}` (선택) |
| 버전 | 1.0.0 |
| 라이선스 | MIT |

### 2.2 설치 방법

```bash
# npm (권장)
npm install -g {PROJECT_NAME}

# npx (설치 없이)
npx {PROJECT_NAME}@latest <command>

# pip (Python)
pip install {PROJECT_NAME}

# uvx (Python, 설치 없이)
uvx {PROJECT_NAME}@latest <command>

# Homebrew (macOS)
brew install {PROJECT_NAME}
```

### 2.3 시스템 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| Node.js | 18.x | 20.x LTS |
| OS | Linux, macOS, Windows 10+ | - |
| Shell | bash, zsh, PowerShell | zsh |
| 권한 | 일반 사용자 | - |

---

## 3. 명령어 구조

### 3.1 전체 구조

```
{PROJECT_NAME} [global-options] <command> [command-options] [arguments]

예시:
  mycli --verbose init my-project --template saas
  mycli run --config ./config.json
  mycli help init
```

### 3.2 글로벌 옵션

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--help` | `-h` | 도움말 표시 | - |
| `--version` | `-V` | 버전 표시 | - |
| `--verbose` | `-v` | 상세 출력 | false |
| `--quiet` | `-q` | 최소 출력 | false |
| `--json` | - | JSON 형식 출력 | false |
| `--no-color` | - | 색상 비활성화 | false |
| `--config` | `-c` | 설정 파일 경로 | 자동 탐색 |

### 3.3 명령어 목록

```
{PROJECT_NAME} <command>

Commands:
  init <name>      새 프로젝트 초기화
  run              프로젝트 실행
  build            프로젝트 빌드
  validate         설정 검증
  config           설정 관리
  help [command]   도움말 표시

Run '{PROJECT_NAME} help <command>' for more information.
```

---

## 4. 명령어 상세

### 4.1 init - 프로젝트 초기화

#### 기본 정보

| 항목 | 값 |
|------|-----|
| 우선순위 | P0 |
| 인터랙티브 | 지원 (옵션 없이 실행 시) |
| 멱등성 | 아니오 (기존 파일 덮어쓰기 확인) |

#### 사용법

```bash
{PROJECT_NAME} init <name> [options]
{PROJECT_NAME} init              # 인터랙티브 모드
```

#### 인자 (Arguments)

| 인자 | 필수 | 설명 | 검증 |
|------|------|------|------|
| `name` | 조건부 | 프로젝트 이름 | 1-50자, kebab-case |

#### 옵션 (Options)

| 옵션 | 단축 | 설명 | 기본값 | 값 |
|------|------|------|--------|-----|
| `--template` | `-t` | 템플릿 선택 | `basic` | basic, saas, api, cli |
| `--dir` | `-d` | 생성 디렉토리 | `./<name>` | 경로 |
| `--git` | - | Git 초기화 | true | boolean |
| `--install` | `-i` | 의존성 설치 | false | boolean |
| `--force` | `-f` | 기존 파일 덮어쓰기 | false | boolean |
| `--dry-run` | - | 실제 생성 없이 미리보기 | false | boolean |

#### 인터랙티브 플로우

```
? 프로젝트 이름: my-project
? 템플릿 선택: (화살표로 선택)
  ❯ basic - 기본 템플릿
    saas - SaaS 프로젝트
    api - REST API
    cli - CLI 도구
? Git 저장소 초기화? (Y/n) Y
? 의존성 설치? (y/N) n

✓ 프로젝트 생성 완료: ./my-project
```

#### 출력 예시

**성공:**
```
[INFO] 프로젝트 초기화 시작...
[INFO] 템플릿 적용: saas
[OK] 파일 생성: package.json
[OK] 파일 생성: src/index.ts
[OK] 파일 생성: README.md
[OK] Git 저장소 초기화 완료
[SUCCESS] 프로젝트 생성 완료: ./my-project

다음 단계:
  cd my-project
  npm install
  npm run dev
```

**JSON 출력 (--json):**
```json
{
  "success": true,
  "project": {
    "name": "my-project",
    "path": "/Users/user/my-project",
    "template": "saas"
  },
  "files_created": [
    "package.json",
    "src/index.ts",
    "README.md"
  ],
  "next_steps": [
    "cd my-project",
    "npm install",
    "npm run dev"
  ]
}
```

#### 에러 케이스

| 상황 | Exit Code | 메시지 | 해결 방법 |
|------|-----------|--------|----------|
| 이름 미입력 | 2 | `[ERROR] 프로젝트 이름을 입력하세요` | `mycli init <name>` |
| 잘못된 이름 | 2 | `[ERROR] 프로젝트 이름은 kebab-case만 가능` | 형식 수정 |
| 디렉토리 존재 | 1 | `[ERROR] 디렉토리가 이미 존재합니다` | `--force` 옵션 |
| 템플릿 없음 | 1 | `[ERROR] 템플릿 'xxx'를 찾을 수 없습니다` | 목록 확인 |
| 권한 없음 | 1 | `[ERROR] 디렉토리 생성 권한이 없습니다` | 경로 변경 |

#### 테스트 시나리오

- [ ] `init my-project` → 기본 템플릿으로 생성
- [ ] `init my-project -t saas` → SaaS 템플릿
- [ ] `init my-project --dry-run` → 미리보기만
- [ ] `init` (인자 없이) → 인터랙티브 모드
- [ ] `init existing-dir` → 에러 + --force 안내
- [ ] `init existing-dir --force` → 덮어쓰기 확인 후 진행
- [ ] `init Invalid_Name` → 에러 (kebab-case 아님)
- [ ] `init my-project --json` → JSON 출력

---

### 4.2 run - 프로젝트 실행

#### 기본 정보

| 항목 | 값 |
|------|-----|
| 우선순위 | P0 |
| 작업 디렉토리 | 현재 또는 --dir 지정 |
| 장시간 실행 | 예 (Ctrl+C로 중단) |

#### 사용법

```bash
{PROJECT_NAME} run [options]
```

#### 옵션

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--config` | `-c` | 설정 파일 | 자동 탐색 |
| `--port` | `-p` | 포트 번호 | 3000 |
| `--watch` | `-w` | 파일 변경 감시 | false |
| `--env` | `-e` | 환경 (dev/prod) | dev |

#### 출력 예시

**시작:**
```
[INFO] 설정 로드: ./config.json
[INFO] 환경: development
[INFO] 서버 시작...

  ✓ 서버 실행 중: http://localhost:3000

  단축키:
    r - 재시작
    o - 브라우저 열기
    q - 종료
```

**Watch 모드:**
```
[WATCH] 파일 변경 감지: src/index.ts
[INFO] 재시작 중...
[OK] 재시작 완료 (0.5s)
```

**종료 (Ctrl+C):**
```
^C
[INFO] 종료 신호 수신...
[INFO] 정리 작업 중...
[OK] 정상 종료
```

#### 에러 케이스

| 상황 | Exit Code | 메시지 |
|------|-----------|--------|
| 설정 파일 없음 | 1 | `[ERROR] 설정 파일을 찾을 수 없습니다` |
| 포트 사용 중 | 1 | `[ERROR] 포트 3000이 사용 중입니다` |
| 설정 오류 | 1 | `[ERROR] 설정 검증 실패: ...` |

#### 시그널 처리

| 시그널 | 동작 |
|--------|------|
| SIGINT (Ctrl+C) | 정리 후 종료, exit 130 |
| SIGTERM | 즉시 종료, exit 143 |
| SIGHUP | 설정 재로드 |

---

### 4.3 build - 프로젝트 빌드

#### 기본 정보

| 항목 | 값 |
|------|-----|
| 우선순위 | P1 |
| 출력 | dist/ 디렉토리 |

#### 사용법

```bash
{PROJECT_NAME} build [options]
```

#### 옵션

| 옵션 | 단축 | 설명 | 기본값 |
|------|------|------|--------|
| `--outdir` | `-o` | 출력 디렉토리 | `./dist` |
| `--minify` | `-m` | 코드 압축 | true (prod) |
| `--sourcemap` | - | 소스맵 생성 | false |
| `--target` | - | 빌드 타겟 | `node18` |
| `--clean` | - | 기존 출력 삭제 | true |

#### 출력 예시

```
[INFO] 빌드 시작...
[INFO] 타겟: node18
[INFO] 출력: ./dist

  Building...
  ████████████████████████████████████████ 100%

[OK] 빌드 완료 (2.3s)

  출력 파일:
    dist/index.js      45 KB
    dist/index.js.map  128 KB
    dist/cli.js        12 KB

  총 크기: 185 KB
```

#### 프로그레스 표시

```typescript
// 프로그레스 바 스펙
interface ProgressBar {
  format: '  {task}...\n  {bar} {percentage}%';
  width: 40;
  complete: '█';
  incomplete: '░';
}
```

---

### 4.4 validate - 설정 검증

#### 기본 정보

| 항목 | 값 |
|------|-----|
| 우선순위 | P1 |
| 용도 | CI/CD 파이프라인 |

#### 사용법

```bash
{PROJECT_NAME} validate [options]
```

#### 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--config` | 설정 파일 | 자동 탐색 |
| `--strict` | 엄격 모드 (경고도 실패) | false |

#### 출력 예시

**성공:**
```
[INFO] 설정 검증 중: ./config.json

  ✓ 스키마 검증 통과
  ✓ 필수 필드 존재
  ✓ 값 범위 정상

[SUCCESS] 설정이 유효합니다
```

**실패:**
```
[INFO] 설정 검증 중: ./config.json

  ✗ 스키마 검증 실패

  에러:
    - port: 숫자여야 합니다 (현재: "3000")
    - name: 필수 필드입니다

  경고:
    - timeout: 권장 범위 초과 (1000-30000)

[FAIL] 설정 검증 실패 (2 에러, 1 경고)
```

#### Exit Code

| 상황 | Exit Code |
|------|-----------|
| 성공 | 0 |
| 에러 있음 | 1 |
| 경고만 (--strict) | 1 |
| 경고만 (기본) | 0 |

---

### 4.5 config - 설정 관리

#### 사용법

```bash
{PROJECT_NAME} config <subcommand> [options]

Subcommands:
  list              모든 설정 표시
  get <key>         특정 설정 조회
  set <key> <value> 설정 변경
  unset <key>       설정 삭제
  path              설정 파일 경로 표시
  init              설정 파일 생성
```

#### 서브커맨드 상세

**config list:**
```
$ mycli config list

현재 설정:
  port: 3000
  verbose: false
  template: basic

설정 파일: ~/.config/mycli/config.json
```

**config get:**
```
$ mycli config get port
3000
```

**config set:**
```
$ mycli config set port 8080
[OK] 설정 변경: port = 8080
```

---

### 4.6 help - 도움말

#### 사용법

```bash
{PROJECT_NAME} help [command]
{PROJECT_NAME} --help
{PROJECT_NAME} <command> --help
```

#### 출력 형식

```
{PROJECT_NAME} - [한 줄 설명]

Usage:
  {PROJECT_NAME} [options] <command> [command-options]

Commands:
  init <name>      새 프로젝트 초기화
  run              프로젝트 실행
  build            프로젝트 빌드
  validate         설정 검증
  config           설정 관리
  help             도움말 표시

Global Options:
  -h, --help       도움말 표시
  -V, --version    버전 표시
  -v, --verbose    상세 출력
  -q, --quiet      최소 출력
  --json           JSON 형식 출력
  --no-color       색상 비활성화

Examples:
  $ {PROJECT_NAME} init my-project
  $ {PROJECT_NAME} run --port 8080
  $ {PROJECT_NAME} build --minify

Documentation:
  https://github.com/user/{PROJECT_NAME}

Report bugs:
  https://github.com/user/{PROJECT_NAME}/issues
```

---

## 5. Constraints (AI 경계)

### ALWAYS (무조건 실행)

- [ ] 모든 입력 검증 (인자, 옵션 타입/범위)
- [ ] 에러 시 0이 아닌 exit code 반환
- [ ] `--help`에 모든 옵션 설명 포함
- [ ] 에러 메시지에 해결 방법 포함
- [ ] 장시간 작업에 프로그레스 표시
- [ ] Ctrl+C 시 정리 작업 후 종료
- [ ] 색상 비활성화 옵션 지원 (CI 환경)
- [ ] stderr로 에러 출력 (stdout과 분리)

### ASK FIRST (확인 후 실행)

- [ ] 파일 덮어쓰기 (--force 없이)
- [ ] 새 의존성 추가
- [ ] 파괴적 작업 (삭제, 초기화)
- [ ] 네트워크 요청

### NEVER (절대 금지)

- [ ] **스펙에 없는 명령어/옵션 구현**
- [ ] 하드코딩된 절대 경로
- [ ] root/admin 권한 요구
- [ ] 에러 무시 (조용히 실패)
- [ ] 확인 없이 파일 삭제/수정
- [ ] 동기 블로킹 작업 (긴 작업)
- [ ] 민감 정보 stdout 출력

### Out of Scope (이번 버전에서 안 함)

| 기능 | 이유 | 추가 예정 |
|------|------|----------|
| GUI | CLI 도구 | 미정 |
| 자동 업데이트 | 복잡도 | v2.0 |
| 플러그인 시스템 | MVP 범위 | v2.0 |
| 원격 설정 동기화 | 복잡도 | v3.0 |

---

## 6. 출력 형식

### 6.1 메시지 형식

```typescript
// 메시지 타입별 형식
const MESSAGE_FORMAT = {
  INFO:    '[INFO]',     // 파란색
  OK:      '[OK]',       // 녹색
  SUCCESS: '[SUCCESS]',  // 녹색 + 볼드
  WARN:    '[WARN]',     // 노란색
  ERROR:   '[ERROR]',    // 빨간색
  DEBUG:   '[DEBUG]',    // 회색 (--verbose 시)
};
```

### 6.2 색상 사용

```typescript
// 색상 팔레트
const COLORS = {
  primary: 'cyan',      // 주요 정보
  success: 'green',     // 성공
  warning: 'yellow',    // 경고
  error: 'red',         // 에러
  muted: 'gray',        // 부가 정보
  highlight: 'bold',    // 강조
};

// --no-color 시 모두 비활성화
```

### 6.3 테이블 출력

```
┌─────────────┬──────────┬──────────┐
│ Name        │ Status   │ Size     │
├─────────────┼──────────┼──────────┤
│ index.js    │ created  │ 45 KB    │
│ cli.js      │ created  │ 12 KB    │
└─────────────┴──────────┴──────────┘
```

### 6.4 스피너

```typescript
// 장시간 작업 시 스피너
const spinner = {
  frames: ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'],
  interval: 80,
};

// 표시
// ⠋ 파일 복사 중...
// ✓ 파일 복사 완료
```

### 6.5 프로그레스 바

```
  빌드 중...
  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░ 40% | 4/10 파일
```

### 6.6 Exit Codes

| 코드 | 상황 | 사용 |
|------|------|------|
| 0 | 성공 | 정상 완료 |
| 1 | 일반 에러 | 실행 중 오류 |
| 2 | 잘못된 사용법 | 인자/옵션 오류 |
| 126 | 권한 없음 | 실행 권한 |
| 127 | 명령어 없음 | 잘못된 커맨드 |
| 130 | SIGINT | Ctrl+C |
| 143 | SIGTERM | 종료 신호 |

---

## 7. 설정 시스템

### 7.1 설정 우선순위

```
1. 명령줄 옵션 (최우선)
   ↓
2. 환경변수 (MYCLI_*)
   ↓
3. 로컬 설정 (.myclirc, mycli.config.json)
   ↓
4. 사용자 설정 (~/.config/mycli/config.json)
   ↓
5. 시스템 설정 (/etc/mycli/config.json)
   ↓
6. 기본값
```

### 7.2 설정 파일 형식

**JSON:**
```json
{
  "$schema": "https://mycli.dev/schema.json",
  "port": 3000,
  "verbose": false,
  "template": "basic",
  "build": {
    "outdir": "./dist",
    "minify": true
  }
}
```

**YAML (.myclirc):**
```yaml
port: 3000
verbose: false
template: basic
build:
  outdir: ./dist
  minify: true
```

### 7.3 설정 스키마

```typescript
interface Config {
  // 기본 설정
  port: number;           // 1024-65535, default: 3000
  verbose: boolean;       // default: false
  template: 'basic' | 'saas' | 'api' | 'cli';  // default: 'basic'

  // 빌드 설정
  build: {
    outdir: string;       // 상대/절대 경로
    minify: boolean;      // default: true (prod)
    sourcemap: boolean;   // default: false
    target: string;       // default: 'node18'
  };

  // 실행 설정
  run: {
    watch: boolean;       // default: false
    env: 'dev' | 'prod';  // default: 'dev'
  };
}
```

### 7.4 환경변수 매핑

| 환경변수 | 설정 키 | 타입 |
|----------|---------|------|
| `MYCLI_PORT` | `port` | number |
| `MYCLI_VERBOSE` | `verbose` | boolean |
| `MYCLI_TEMPLATE` | `template` | string |
| `MYCLI_BUILD_OUTDIR` | `build.outdir` | string |

---

## 8. 인터랙티브 모드

### 8.1 프롬프트 타입

```typescript
// 텍스트 입력
{
  type: 'input',
  name: 'projectName',
  message: '프로젝트 이름:',
  validate: (input) => /^[a-z][a-z0-9-]*$/.test(input) || '형식 오류'
}

// 선택
{
  type: 'select',
  name: 'template',
  message: '템플릿 선택:',
  choices: [
    { title: 'basic', description: '기본 템플릿' },
    { title: 'saas', description: 'SaaS 프로젝트' }
  ]
}

// 확인
{
  type: 'confirm',
  name: 'git',
  message: 'Git 초기화?',
  initial: true
}

// 다중 선택
{
  type: 'multiselect',
  name: 'features',
  message: '기능 선택:',
  choices: [...]
}
```

### 8.2 키 바인딩

| 키 | 동작 |
|-----|------|
| ↑/↓ | 항목 이동 |
| Enter | 선택 확정 |
| Space | 토글 (다중 선택) |
| Esc | 취소 |
| Ctrl+C | 중단 |

### 8.3 비인터랙티브 환경 감지

```typescript
// CI 환경 감지
const isCI = process.env.CI ||
             process.env.CONTINUOUS_INTEGRATION ||
             !process.stdin.isTTY;

if (isCI) {
  // 인터랙티브 프롬프트 스킵
  // 기본값 또는 에러 반환
}
```

---

## 9. 기술 스택

### 9.1 언어 & 런타임

| 구분 | 선택 | 버전 | 이유 |
|------|------|------|------|
| 언어 | TypeScript | 5.3+ | 타입 안전성 |
| 런타임 | Node.js | 20 LTS | 안정성 |
| 패키지 매니저 | pnpm | 8.x | 속도, 디스크 효율 |

### 9.2 CLI 프레임워크

| 구분 | 선택 | 이유 |
|------|------|------|
| CLI 파싱 | Commander.js / yargs | 성숙도 |
| 인터랙티브 | Inquirer / prompts | 사용성 |
| 출력 | chalk / picocolors | 색상 |
| 스피너 | ora | 사용자 피드백 |
| 테이블 | cli-table3 | 구조화된 출력 |

### 9.3 배포

| 채널 | 패키지 | 명령어 |
|------|--------|--------|
| npm | {PROJECT_NAME} | `npm install -g` |
| Homebrew | {PROJECT_NAME} | `brew install` |
| Binary | GitHub Releases | 직접 다운로드 |

---

## 10. 에러 처리

### 10.1 에러 클래스

```typescript
// 커스텀 에러 클래스
class CLIError extends Error {
  constructor(
    message: string,
    public code: string,
    public exitCode: number = 1,
    public suggestion?: string
  ) {
    super(message);
  }
}

// 사용 예
throw new CLIError(
  '설정 파일을 찾을 수 없습니다',
  'CONFIG_NOT_FOUND',
  1,
  'mycli config init 으로 생성하세요'
);
```

### 10.2 에러 출력 형식

```
[ERROR] 설정 파일을 찾을 수 없습니다

  원인: ./config.json 파일이 존재하지 않습니다

  해결 방법:
    mycli config init    설정 파일 생성
    mycli run -c <path>  다른 경로 지정

  문서: https://mycli.dev/docs/config
```

### 10.3 디버그 모드

```bash
# 환경변수
DEBUG=mycli:* mycli run

# 또는 옵션
mycli run --verbose
```

**디버그 출력:**
```
[DEBUG] 설정 로드 시작
[DEBUG] 탐색 경로: ['./.myclirc', './mycli.config.json', ...]
[DEBUG] 발견: ./mycli.config.json
[DEBUG] 파싱 완료: { port: 3000, ... }
```

---

## 11. Shell Completion

### 11.1 생성 명령어

```bash
# Bash
mycli completion bash >> ~/.bashrc

# Zsh
mycli completion zsh >> ~/.zshrc

# Fish
mycli completion fish > ~/.config/fish/completions/mycli.fish

# PowerShell
mycli completion powershell >> $PROFILE
```

### 11.2 완성 예시

```bash
$ mycli in<TAB>
init

$ mycli init --<TAB>
--template  --dir  --git  --install  --force  --dry-run

$ mycli init --template <TAB>
basic  saas  api  cli
```

---

## 12. 테스트 전략

### 12.1 테스트 종류

| 종류 | 커버리지 | 도구 |
|------|---------|------|
| Unit | 80% | Vitest |
| Integration | 주요 명령어 | Vitest |
| E2E | 핵심 플로우 | CLI 실행 |
| Snapshot | 출력 형식 | Vitest |

### 12.2 명령어별 테스트 케이스

**init:**
- [ ] 기본 실행 → 성공
- [ ] --template 옵션 → 해당 템플릿 적용
- [ ] 기존 디렉토리 → 에러 + --force 안내
- [ ] --force → 덮어쓰기
- [ ] --dry-run → 미리보기만
- [ ] 잘못된 이름 → 검증 에러
- [ ] --json → JSON 출력

**run:**
- [ ] 기본 실행 → 서버 시작
- [ ] --port → 지정 포트
- [ ] 설정 없음 → 에러
- [ ] Ctrl+C → 정상 종료

### 12.3 크로스 플랫폼 테스트

| OS | 테스트 환경 |
|-----|------------|
| Linux | GitHub Actions |
| macOS | GitHub Actions |
| Windows | GitHub Actions (PowerShell) |

---

## 13. 완료 정의 (DoD)

### 13.1 명령어별 DoD

| 명령어 | 완료 조건 |
|--------|----------|
| init | 모든 템플릿 생성, 인터랙티브 동작 |
| run | 서버 시작, watch 모드, 정상 종료 |
| build | 빌드 성공, sourcemap, minify |
| validate | 스키마 검증, 에러/경고 구분 |
| config | CRUD 동작 |
| help | 모든 명령어 도움말 |

### 13.2 전체 DoD

- [ ] 모든 P0 명령어 동작
- [ ] --help 완성
- [ ] --version 동작
- [ ] 에러 메시지에 해결 방법 포함
- [ ] 테스트 커버리지 80%
- [ ] 크로스 플랫폼 테스트 통과
- [ ] README 문서화
- [ ] Shell Completion 지원
- [ ] npm 배포 완료

---

## 14. 마일스톤

| 단계 | 내용 | 완료 조건 |
|------|------|-----------|
| M1 | 프로젝트 설정 | CLI 프레임워크, 빌드 설정 |
| M2 | 기본 명령어 | help, version |
| M3 | init | 템플릿 시스템, 인터랙티브 |
| M4 | run/build | 핵심 기능 |
| M5 | config/validate | 설정 관리 |
| M6 | 테스트 & 문서 | 커버리지 80%, README |
| M7 | 배포 | npm 퍼블리시 |

---

## 변경 로그

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|----------|--------|
| {DATE} | 1.0 | 최초 작성 | |

---

## 부록: Man Page 구조

```
NAME
    {PROJECT_NAME} - [한 줄 설명]

SYNOPSIS
    {PROJECT_NAME} [options] <command> [command-options]

DESCRIPTION
    [상세 설명]

COMMANDS
    init <name>
        새 프로젝트 초기화

    run
        프로젝트 실행

OPTIONS
    -h, --help
        도움말 표시

    -V, --version
        버전 표시

ENVIRONMENT
    MYCLI_PORT
        기본 포트 번호

FILES
    ~/.config/mycli/config.json
        사용자 설정 파일

EXAMPLES
    $ {PROJECT_NAME} init my-project
    $ {PROJECT_NAME} run --port 8080

SEE ALSO
    {PROJECT_NAME}-init(1), {PROJECT_NAME}-run(1)

BUGS
    https://github.com/user/{PROJECT_NAME}/issues
```
