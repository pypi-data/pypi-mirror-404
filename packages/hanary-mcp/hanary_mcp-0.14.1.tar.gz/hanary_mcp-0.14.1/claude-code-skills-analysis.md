# Claude Code Skills 기능 분석

> Task 753: hanary skills 만들기 위한, claud code 의 skills 기능 조사, 분석
> 작성일: 2026-01-21

## 1. Skills란?

Skills는 Claude Code의 **재사용 가능한 프롬프트 템플릿 시스템**으로, 특정 도메인이나 작업에 대한 전문화된 지식과 워크플로우를 패키징한 것.

### 핵심 특징
- **재사용 가능한 프롬프트 템플릿**: 슬래시 명령어로 트리거
- **워크플로우 자동화**: 여러 단계를 결합
- **커스텀 확장**: 사용자 필요에 맞는 기능 추가

## 2. Skill 구조

```
skill-name/
├── SKILL.md (필수)
│   ├── YAML frontmatter (name, description 필수)
│   └── Markdown 지침
└── Bundled Resources (선택)
    ├── scripts/       - 실행 가능한 코드 (Python/Bash)
    ├── references/    - 필요시 로드되는 참조 문서
    ├── examples/      - 실제 작동하는 예제
    └── assets/        - 출력에 사용되는 파일 (템플릿, 이미지 등)
```

### 2.1 SKILL.md 파일 구조

```yaml
---
name: skill-name
description: This skill should be used when the user asks to "create X", "configure Y", or mentions "Z"...
version: 0.1.0
---

# Skill Title

## Overview
스킬의 목적 설명

## When to Use
어떤 상황에서 사용하는지

## Instructions
구체적인 지침과 워크플로우

## Additional Resources
### Reference Files
- **`references/patterns.md`** - 상세 패턴
- **`references/advanced.md`** - 고급 기법
```

## 3. Progressive Disclosure (점진적 공개)

Skills는 3단계 로딩 시스템으로 컨텍스트를 효율적으로 관리:

| Level | 내용 | 로딩 시점 | 크기 |
|-------|------|----------|------|
| 1 | Metadata (name + description) | 항상 | ~100 words |
| 2 | SKILL.md body | Skill 트리거 시 | <5k words |
| 3 | Bundled resources | 필요시 | 무제한* |

*무제한: scripts는 컨텍스트에 로드하지 않고 실행 가능

## 4. Plugin 구조 (Skills를 포함하는 상위 개념)

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json      # 플러그인 메타데이터
├── commands/            # 사용자가 호출하는 슬래시 명령어
│   └── my-command.md
├── agents/              # Claude가 생성하는 서브에이전트
│   └── my-agent.md
└── skills/              # 자동으로 트리거되는 컨텍스트 가이드
    └── my-skill/
        ├── SKILL.md
        ├── references/
        ├── examples/
        └── scripts/
```

### 4.1 Commands vs Skills vs Agents

| Type | 호출 방식 | 위치 | 용도 |
|------|----------|------|------|
| **Commands** | 사용자 직접 호출 (`/command`) | `commands/` | 명시적 작업 수행 |
| **Skills** | Claude 자동 호출 (컨텍스트 기반) | `skills/` | 컨텍스트 가이드 제공 |
| **Agents** | Claude가 spawn | `agents/` | 특화된 서브태스크 처리 |

## 5. Skill 작성 가이드라인

### 5.1 Description 작성 규칙
- **Third-person 사용**: "This skill should be used when..."
- **구체적 트리거 문구 포함**: "create X", "configure Y" 등
- **명확한 시나리오 나열**

```yaml
# 좋은 예
description: This skill should be used when the user asks to "create a hook", "add a PreToolUse hook", or mentions hook events.

# 나쁜 예
description: Use this skill when working with hooks.  # Wrong person, vague
```

### 5.2 Body 작성 규칙
- **Imperative/Infinitive form 사용**: "To do X, perform Y"
- **Second person 금지**: "You should..." 대신 "To accomplish X, do Y"
- **간결하게 유지**: 1,500-2,000 words 권장, 최대 5,000 words

```markdown
# 좋은 예
To create a hook, define the event type first.
Configure the server with authentication credentials.

# 나쁜 예
You should create a hook by defining the event type.
You need to configure the server.
```

## 6. 기본 제공 Skills

### Document Creation
- `docx` - Word 문서 생성/편집
- `xlsx` - Excel 스프레드시트 작업
- `pptx` - PowerPoint 프레젠테이션
- `pdf` - PDF 조작

### Development
- `mcp-builder` - MCP 서버 생성
- `skill-creator` - 새 Skill 생성
- `webapp-testing` - Playwright 테스트

### Design
- `frontend-design` - UI 컴포넌트 생성
- `canvas-design` - 시각적 디자인
- `algorithmic-art` - p5.js 생성 아트

## 7. Hanary Skills 적용 방안

### 7.1 Hanary에 필요한 Skills 후보

| Skill 이름 | 용도 | 트리거 조건 |
|-----------|------|------------|
| `hanary-task` | 작업 관리 워크플로우 | "create task", "manage tasks" |
| `hanary-squad` | 스쿼드 관리 | "create squad", "squad settings" |
| `hanary-elixir` | Phoenix/Elixir 코딩 가이드 | LiveView, Ecto 관련 |
| `hanary-ui` | Tailwind UI 패턴 | 컴포넌트 스타일링 |

### 7.2 구현 방향

1. **프로젝트 레벨 Skills** (`.claude/skills/`)
   - Hanary 프로젝트 전용 Skills
   - Phoenix/LiveView 패턴
   - UI 컴포넌트 가이드라인

2. **Global Skills** (`~/.claude/skills/`)
   - 범용적으로 사용 가능한 Skills
   - 개인 워크플로우 자동화

### 7.3 예시: hanary-liveview Skill 구조

```
skills/
└── hanary-liveview/
    ├── SKILL.md
    │   - LiveView 패턴 개요
    │   - 기본 워크플로우
    │   - 빠른 참조
    ├── references/
    │   ├── components.md      # 컴포넌트 패턴
    │   ├── streams.md         # 스트림 사용법
    │   └── forms.md           # 폼 처리
    ├── examples/
    │   ├── task-list.ex       # 태스크 리스트 예제
    │   └── modal.ex           # 모달 예제
    └── scripts/
        └── validate.sh        # 유효성 검사
```

## 8. 구현 체크리스트

### Skill 생성 시 확인사항

- [ ] SKILL.md 파일 존재, 유효한 YAML frontmatter
- [ ] `name`과 `description` 필드 존재
- [ ] Description이 third-person으로 작성
- [ ] 구체적인 트리거 문구 포함
- [ ] Body가 imperative form으로 작성
- [ ] SKILL.md가 간결 (1,500-2,000 words)
- [ ] 상세 내용은 references/로 분리
- [ ] 참조되는 파일이 실제로 존재
- [ ] 예제가 완전하고 작동함

## 9. 참고 자료

- [Claude Code Skills Docs](https://code.claude.com/docs/en/skills)
- [How to create custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)
- [Skills Best Practices](https://www.claude.com/blog/how-to-create-skills-key-steps-limitations-and-examples)
- 로컬 예제: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/skills/`

## 10. 결론

Claude Code의 Skills 시스템은 **재사용 가능한 전문 지식을 패키징**하여 특정 도메인에서 Claude의 효과를 높이는 강력한 메커니즘이다.

Hanary 프로젝트에 적용 시:
1. Phoenix/LiveView 패턴을 Skills로 문서화
2. UI 컴포넌트 가이드라인 제공
3. 프로젝트 특화 워크플로우 자동화

이를 통해 일관된 코드 품질과 개발 효율성 향상을 기대할 수 있다.
