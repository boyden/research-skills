[English](README.md) | **简体中文**

# research-skills

科研产出用的 Claude Code skill 集合：从分析结果出汇报 deck，以后加写论文等。

## 结构

```
shared/                      跨 skill 的共同规则，各 skill 引用、不重复抄
  numbers-and-sources.md     数字溯源、效应量写法、多重检验措辞
  figures.md                 按最终尺寸画图、字体、配色、KM / ROC / 森林图、示意图、开放许可图标
  tables.md                  三线表（matplotlib / pptxgenjs / LaTeX / Word 的实现）
  writing-style.md           标题与结论句、照原样用用户的说法、人名、缩写、版本命名
skills/
  results-deck/              从分析结果出 pptx deck
    SKILL.md                 入口：工作流、每页规则、什么时候停下来问
    reference/               大纲格式、页型目录、检查清单
    engine/                  可复用的 v2 构建器、主题、画图和验证工具
      SPEC.md                engine 接口约定
      template/              可复制的 deck 骨架
examples/                    公开数据（GBSG2）画的示例图、开放许可图标（CC0 / ISC / MIT / CC BY，逐个登记在 examples/icons/manifest.csv），以及生成示例图的脚本
```

计划中：
- `skills/paper-writing/`：写论文的 skill；
- `.claude-plugin/`：插件 manifest，用来在别的机器上一次装好。

## 在 Claude Code 里使用

插件 manifest 还没写，暂时用软链接把 skill 放进用户级 skill 目录，所有项目都能用：

```bash
ln -s /path/to/research-skills/skills/results-deck ~/.claude/skills/results-deck
```

SKILL.md 用相对路径 `../../shared/` 引用共同规则。软链接只解析到真实目录，所以链接整个 skill 目录就行，
不要只拷 SKILL.md 一个文件出去。

## 约定

- 文档有两版：英文 `X.md`（GitHub 默认显示）和中文 `X.zh-CN.md`。改其中一版时，在同一次改动里同步另一版。
- 所有生成的产出物都用英文：slide 和图中文字、表格、Source 行、speaker notes、PPTX、PDF 和预览图。
- 图、上屏文字、speaker notes、代码标识符、文件名和代码注释用英文。
- 面向用户的 engine、template、reference 和 skill 文档都遵守 `X.md` / `X.zh-CN.md` 成对维护的约定。
- 这里只放通用的东西。单位的模板 pptx、logo、受许可限制的字体，以及项目专用的统计口径，都留在各项目里。
- 外部图标和图片只用开放许可的，并在 `examples/README.md` 或使用它的项目里登记来源和许可。
