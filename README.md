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
examples/                    公开数据（GBSG2）画的示例图、开放许可图标（CC0 / ISC / MIT / CC BY，逐个登记在 examples/icons/manifest.csv），以及生成示例图的脚本
```

计划中：
- `skills/results-deck/engine/`：可复用的 pptxgenjs 版式元素、构建脚本和检查工具，外加一个能直接 build 的小骨架；
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

- 文档用中文；图、上屏文字和代码注释用英文。
- 这里只放通用的东西。单位的模板 pptx、logo、受许可限制的字体，以及项目专用的统计口径，都留在各项目里。
- 外部图标和图片只用开放许可的，并在 `examples/README.md` 或使用它的项目里登记来源和许可。
