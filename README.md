# create-handdrawn-mv · 手书与角色 MV 制作

一个用于 **AI 辅助角色手书、关键画拼贴与有限动画** 的技能包，以及两套实际工程中保留下来的 Python / ModernGL / GLSL 工具。

核心方法：先设计每个镜头的动作，再制作成对 A/B 关键画，分层合成，最后分别检查素材、动作、转场和编码文件。两张关键画不等于完整逐帧动画；自动检查通过也不等于视觉质量通过。

## 仓库内容与完整性

- **完整技能包**：根目录的 `SKILL.md`、`agents/`、`assets/`、`references/`、`scripts/`，来自现有技能的真实源文件。案例文档已移除私人文件标识与恢复入口。
- **通用检查器**：`scripts/check_project.py`，检查分镜、素材、素材使用记录和成片技术参数。
- **原始工程工具**：`examples/sweet-reverie/` 与 `examples/paper-handdrawn/`，保留实际渲染脚本、shader、时间线及第三方许可，不是重新编写的替代实现。
- **不包含媒体工程**：不附角色立绘、参考截图、音乐、成片、字体二进制或私人制作记录。示例渲染器需要自行准备有权使用的素材。

两个源工程 ZIP 均缺少完整的 ZIP 目录/结尾。已收录的源码文件逐个通过解压长度和 CRC 校验；不能因此宣称原 ZIP 完整，或原影片已在本仓库端到端复现。详见 [来源与完整性](SOURCE_PROVENANCE.md)。

## 安装技能

本仓库根目录就是技能目录，`SKILL.md` 应与 `references/`、`scripts/`、`assets/` 一起安装。

### Codex 的技能安装器

在支持 `$skill-installer` 的 Codex 中提出：

> 安装 https://github.com/youngstudent2/create-handdrawn-mv 的根目录技能，名称为 create-handdrawn-mv。

如果直接使用技能安装器脚本，可指定仓库根路径和名称：

```bash
python /path/to/skill-installer/scripts/install-skill-from-github.py \
  --repo youngstudent2/create-handdrawn-mv --path . --name create-handdrawn-mv
```

安装器默认使用 `$CODEX_HOME/skills`（通常为 `~/.codex/skills`）。已有同名技能时，先确认更新方式，不要直接覆盖自己的修改。安装后的下一轮对话可调用技能。其他支持 `SKILL.md` 的产品，请按其当前安装流程导入完整目录。

### 仅运行检查工具

不安装技能也能使用检查脚本：

```bash
git clone https://github.com/youngstudent2/create-handdrawn-mv.git
cd create-handdrawn-mv
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/check_project.py assets/storyboard.example.json --plan-only
```

Python 3；计划检查仅依赖标准库。图片检查需要 Pillow；视频检查需要系统中的 `ffprobe`，完整解码需要 `ffmpeg`。本次测试环境为 Python 3.12。

## 调用示例

> 使用 $create-handdrawn-mv，参考我提供的视频和角色设定，制作 30 秒角色手书。先设计逐镜头动作，每镜头至少两张有实际动作差异的关键画，再试渲染最难的动作和转场。保留素材来源与提示词记录。

返修时可以提供问题帧和现有工程：

> 使用 $create-handdrawn-mv 检查这些镜头的人体、手指与姿势切换。先区分原画错误和合成重影，修复后检查切点前后连续帧，并去掉指定片尾文字。

技能会使用当前环境实际可用的图像生成和合成工具。仓库本身不提供图像生成 API 客户端，不包含 API 密钥，也不会仅凭分镜 JSON 自动生成完整电影。

## 最小工作流程

1. 将 `assets/storyboard.example.json` 复制为自己的 `project.json`，按实际音乐和叙事改写；素材路径相对这个 JSON 所在目录。
2. 运行计划检查，确认时间线连续、镜头动作与关键画数量正确。
3. 制作并逐张查看 A/B 立绘，保持身份、画布、机位和支点一致；大动作增加中间画。
4. 用自己的编辑器或示例合成器试渲染；不同示例的输入格式不完全相同，见各自说明。
5. 从渲染器记录真实使用过的素材，再检查最终编码视频并人工观看。

```bash
python scripts/check_project.py project.json --plan-only
python scripts/check_project.py project.json \
  --contact-sheet output/keyframes.jpg --report output/assets.json
python scripts/check_project.py project.json \
  --video output/final.mp4 --usage output/usage.json --decode \
  --report output/final-check.json
```

示例 JSON 只有分镜结构，没有对应图片和音轨。直接对模板运行完整素材检查，出现“文件缺失”是预期行为。

检查器返回码：`0` 表示所运行的自动检查没有错误；`1` 表示检查失败；参数组合错误通常为 `2`。姿势语义、手部解剖、角色一致性、遮挡、节拍与音画同步仍须人工检查。详见 [检查范围](references/validation.md)。

## 两套工程工具

- [Sweet Reverie：19 镜 / 38 张关键画的拼贴合成工具](examples/sweet-reverie/README.md)
- [纸感手书：12 镜 / 24 张关键画的修正版工具](examples/paper-handdrawn/README.md)

它们是有具体镜头设计和资源约定的原始工程代码，不是通用视频编辑器。较早的 Sweet Reverie 合成器仍保留短 A/B 溶解；后续技能已明确指出，轮廓不同的手和身体不应靠溶解解决动作连续性。新制作请以当前技能与返修指南为准。

## 测试

```bash
python -m unittest discover -s tests -v
```

测试覆盖分镜模板、无效分镜及命令行参数，不调用外部付费 API，不使用角色图或音乐素材；不包含视频或 GPU 测试。测试结果与未覆盖范围见 [TESTING.md](TESTING.md)。

## 来源、署名与许可

技能和自编工程代码没有提供独立的项目级许可证，本仓库没有擅自补加 MIT 等许可。第三方代码按其原有许可保留：GL Transitions 大部分为 MIT，`InvertedPageCurl.glsl` 为 BSD-3-Clause；字体许可文本为 SIL OFL-1.1，但不附字体文件。见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

角色、参考视频及音乐的署名与权利归各自权利人；公开代码不代表拥有这些媒体的再发布或商用许可。请为自己的素材单独确认使用范围。

---

## English summary

A complete Chinese-language agent skill for character hand-drawn music videos, paired-pose cutout animation, and animation repair, plus recovered original Python/ModernGL/GLSL production tools. The repository root is the installable skill. The validator can be used independently. Character artwork, reference footage, music, movies, private records, and font binaries are excluded. The two example projects require separately supplied assets and have not been reproduced end to end here. No new license has been assigned to the original project code; third-party notices are preserved.
