# 双Agent协作开发系统

基于 OpenCode 的双 Agent 协作框架，实现产品经理与开发的分离式协作。

## 目录结构

```
dual-agent-collaboration-system/
├── docs/
│   ├── 01-requirements/          # 需求阶段文档
│   │   ├── requirements_v*.md    # 需求文档
│   │   ├── system_design_v*.md   # 系统设计
│   │   ├── requirements_review_*.md  # 评审意见
│   │   └── requirements_signoff.md    # 签署确认
│   ├── 02-design/                # 设计阶段文档
│   ├── 03-test/                  # 测试阶段文档
│   ├── 04-changelog/             # 变更记录
│   └── COLLABORATION_GUIDE.md    # 协作流程指南
├── state/
│   └── project_state.yaml        # 项目状态文件
├── src/                          # 源代码
├── scripts/                      # 辅助脚本
└── .gitignore
```

## 快速开始

### Agent 1 (产品经理) 初始化项目
```bash
cd dual-agent-collaboration-system
git pull
# 创建需求文档
# 更新状态文件
git add .
git commit -m "feat(requirements): initial requirements"
git push
```

### Agent 2 (开发) 开始评审
```bash
cd dual-agent-collaboration-system
git pull
# 阅读需求文档
# 创建评审意见
git add .
git commit -m "review(requirements): initial review"
git push
```

## 协作流程

1. **需求评审** → Agent1 创建需求 → Agent2 Review → 双方确认
2. **设计评审** → Agent1 创建设计 → Agent2 Review → 双方确认
3. **开发测试** → Agent2 开发 → Agent1 黑盒测试 → 通过确认
4. **部署发布** → Agent1 部署 → 更新变更记录

## 状态文件

每次操作后更新 `state/project_state.yaml`，记录当前阶段和状态。

## 标签规范

- `requirements-v1-approved` - 需求确认
- `design-v1-approved` - 设计确认
- `test-v1-passed` - 测试通过
- `release-v1.0.0` - 正式发布

## 详细说明

参见 [协作流程指南](docs/COLLABORATION_GUIDE.md)
