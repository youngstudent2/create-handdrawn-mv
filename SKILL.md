---
name: create-handdrawn-mv
description: Create or improve character hand-drawn music videos (手书), anime collage films, and imagegen-assisted character shorts from reference videos and character images. Use for storyboarding, per-shot paired poses, expressive motion, effects and transitions, rendering a finished MP4, or repairing awkward anatomy, malformed hands, pose ghosting, unsuitable transitions, unwanted end-card text, or stiff and repetitive character acting. Especially useful when the user requests two distinct character images per shot. Do not use for ordinary slideshow assembly or video analysis with no production intent.
---

# 手书与角色 MV 制作

把参考片的节奏、镜头语言和角色表演转成可执行的分镜，再制作素材与成片。以“每个镜头发生了什么变化”为设计单位。不能靠增加转场或缩放静态立绘来解决角色表演不足。

## 1. 确认任务与证据

- 沿用用户已给出的角色、来源、风格、时长和修改意见；已有授权内直接推进。只询问真正阻塞制作的问题。
- 检查现有工程与成片，保留已经认可的版本。先确认素材、音轨和工具是否实际可用，再承诺交付。
- 收到问题帧或人体、手指、转场反馈时，先读取 [repair-anatomy-and-transitions.md](references/repair-anatomy-and-transitions.md)，把截图映射到镜头和姿势切换点，区分原画错误、合成重影与动作不连续。
- 实际观看用户参考片，结合抽帧检查节拍、景别、构图、动作、层次和转场。标题、缩略图和文字介绍不能替代观看；无法读取时明确这一点，继续完成有依据的部分。
- 从角色来源提取少量清晰的身份锚点。区分角色设定来源与影片风格来源，避免把风格参考中的人物外貌移植过来。
- 记录音乐来源和截取区间；不要将引用音轨称为原创或推断商用许可。不因假设的风险自行增加审批流程。
- 把工具研究限定在具体缺口：检查本地能力，必要时查官方文档，做短测试，再选择工具。不要用“已了解某工具”代替实际验证。

## 2. 先定表演，再定素材量

读取 [storyboard-and-art.md](references/storyboard-and-art.md)。从 [storyboard.example.json](assets/storyboard.example.json) 复制并改写项目清单。

- 根据音乐和叙事分镜，不机械套用固定镜头数。先把时间线、情绪发展和动作变化写清楚。
- 每个角色表演镜头默认规划至少两张具有可见动作或表情差异的关键立绘 A/B；更复杂的动作增加关键帧或中间帧。
- 若用户要求“每个镜头两张”，则将 `requirements.all_shots_need_character` 设为 `true`，并确保所有镜头都有至少两张独立角色图，特效镜头也不例外。
- `min_character_keyframes` 表示每个角色镜头的最低张数；`unique_assets` 默认 `true`。用户明确允许静态停顿、素材复用或不同数量时，按任务设置并说明计数口径。
- 区分镜头数、独立角色图数和视频帧数。镜像、裁切、换色、缩放、同图重复导出都不算新姿势。19 镜头 × 2 张 = 38 张，是克琪亚粉裙案例的规模，不是所有 30 秒影片的模板。
- 每个镜头写出 A→B 的动作、景别、相机、背景、前景、特效用途、转场、视觉重点和可接受裁切。两张图“看起来不同”不等于动作成立。
- 用 `python scripts/check_project.py project.json --plan-only` 检查结构、时长和计划素材数量，再开始批量生成。

## 3. 制作成对立绘与分层素材

- 使用当前环境内置的图像生成工具并遵循其技能。先查看引用图，优先以已认可的形象锚点生成 A，再以 A 和同一形象锚点编辑 B。每次提交都明确要保留和要改变的部分。
- 锁定身份、服装、画风、光线、画幅和镜头角度；让表情、视线、手势或身体轮廓产生有目的的差异。不要独立随机生成 A/B 后强行拼接。
- 角色素材输出真实透明背景，预留头发、手、裙摆和鞋子的运动空间。需要全身时不可接受缺脚或贴边头发；胸像自然裁切要在合成时使用画框或近景承接。
- 背景、角色、道具、前景分别制作；自然图像用图像生成，精确圆环、文字、遮罩和粒子可用程序绘制。
- 按 `shot_01_A.png` / `shot_01_B.png` 命名，记录实际提示词与来源。保留已认可版本，修复有问题的局部，不轻易全量重做。
- 逐张检查角色一致性、左右饰品、手指、手臂连接、眼睛、服装和透明边缘。数量或哈希检查无法代替这些视觉检查。
- 全身动作先验证肩胯、关节方向、重心和支撑脚；手部先验证手掌朝向、拇指侧、指节与接触关系。不要为了展示五指而强行展开本应被遮挡的手指。修复 A 后，仍以 A 编辑 B 并重新核对动作连续性。
- 并行工作仅在当前规则允许时使用；若分工，把完整 A/B 对分给同一执行者，统一锚点、命名与交接清单。

## 4. 合成有表演和节奏的镜头

读取 [compositing.md](references/compositing.md)，按项目选择工具，不默认绑定某个编辑器。

- 对需要可编程透视、网格变形和 GLSL 转场的拼贴片，可用 ModernGL/EGL 合成与 FFmpeg 编码；简单任务可直接用现有编辑器或 FFmpeg。先试渲染代表镜头与最难的转场。
- 优先表现动作，再叠加相机、景深层次、道具响应与特效。景别和构图也应变化；持续推拉同一立绘不构成充分表演。
- A/B 使用同一画布和同一联合裁切框，保持头部、躯干或指定支点对齐。姿势切换按动作和音乐决定；不要给所有镜头套同一个慢溶解。
- 对轮廓明显不同的手和身体，默认每帧只暴露一个姿势；差异较大时增加中间画或改变动作设计。排查非预期 A→B→A→B 倒退，不用“呼吸”循环反复播放完整手势。站立角色保持支撑脚与地面的关系，不用整个人物的旋转、缩放或网格摆动伪造转身。
- 透明素材混合采用一致的预乘 alpha 约定，检查黑边和双重轮廓。两关键姿势加合成应如实称为关键帧拼贴/有限动画，不能宣称逐帧手绘。
- 把强万花筒、递归画框、扭曲等效果放在背景或独立图层；需要清楚看到动作时，在这些效果之后绘制主体角色。
- 前景丝带、粒子和运动模糊避让脸、手及关键道具。特效应有节奏和用途，也要给观众看清角色的时间。
- 转场方向接续动作或视线，强度随音乐变化；避免每个切点都用同等强度的特效。
- 渲染时记录真正被绘制的素材键及有效显示帧数（如可测）。素材出现在文件夹里，不等于进入成片；进入绘制调用，也不等于最终可见。

## 5. 分阶段验证并交付

1. 检查全量 A/B 素材总览，修复重复姿势、缺失、错手、错饰品和不可用裁切。
2. 渲染低分辨率的短片段，覆盖动作变化、最复杂特效、转场和片尾。观看运动，不只看截图。
3. 在目标尺寸渲染最终片；核对时长、分辨率、帧率、音轨、首尾与完整解码。
4. 运行 `python scripts/check_project.py project.json --video output/final.mp4 --usage output/usage.json --decode --contact-sheet output/keyframes.jpg --report output/qa.json`。依赖 Pillow；视频检查需 FFmpeg/ffprobe。参数与限制见 [validation.md](references/validation.md)。
5. 人工观看整片，特别检查 A/B 是否实际可辨、角色是否被遮挡、节拍与音画同步、姿势切换有无跳位。自动通过不能宣称视觉质量已通过。
6. 交付最终 MP4、素材总览和可复用工程（素材、时间线、代码/工程文件、来源及依赖说明）。按当前环境的持久化规则保存，并提供可打开的成片。用户只要其中部分时尊重范围。

返修时额外从最终编码视频提取问题姿势及每个修改切点前后至少三帧，核对动作顺序、脚位、手部重影、文字和裁切。用户指定删除片尾底部文字时，删除对应文字图层或调用，并在多个片尾时间点检查；不要靠裁掉人物或覆盖画面掩盖。

报告已完成的实际数量、具体改进、检验结果及仍存在的限制。没有运行的工具、没有生成的图、没有观看的视频都不能写成已完成。

## 复用克琪亚案例

仅当任务涉及克琪亚或要求复用本次工程时读取 [cookiya-case.md](references/cookiya-case.md)。保留其中的制作教训，不把该角色、配色、镜头数或音乐强加给新任务。
