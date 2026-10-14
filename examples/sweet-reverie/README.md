# Sweet Reverie 原始合成工具

保留 19 镜头 / 38 张 A/B 关键画的原始 Python、ModernGL 与 GLSL 工具。仅源码恢复，不是媒体齐全的工程。

## 环境与运行

在独立虚拟环境安装 `v3/requirements.txt`；版本为原工程记录，未在所有系统重新验证。需要 FFmpeg（libx264）、OpenGL 3.3+ 和 EGL。原字体路径针对 Linux，其他系统需调整 `compositor.py` 与 `check_assets.py`。

准备自有素材后，从本目录运行 `python v3/render_v3.py --width 1440 --fps 30`。运行前先阅读脚本，首次建议较低分辨率试渲染。

## 缺失的媒体输入

- `v3/assets/shot_01_A.png` 到 `shot_19_B.png`，共 38 张角色关键画。
- 本目录 `assets/` 内 `cosmos_bg.png`、`dream_bg.png`、`theatre_bg.png`、`props_atlas.png`、`props_atlas_v2.png`、`music.m4a`。
- 道具图集裁剪坐标在 `v3/compositor.py` 中硬编码，不能随意换一张图而不调整代码。
- 字体、参考图、生成提示记录、历史 audit 日志未提供。

`shot_plan.json` 是原始画面规划，`production_v3.json` 是原工程元数据；不是根目录检查器的通用 manifest 格式。

`package_project.py` 是历史完整工程打包器，要求媒体、audit 输出和 `v3/README.md` 等文件，当前发布内容不能直接运行它得到原始工程。它会写入元数据并包含素材和提示记录；使用者应在自行打包分享前审核权限及隐私。

早期 A/B 溶解不保证人体动作正确；新制作请采用当前 skill 的动作连续性与返修指南。这里没有声称完整渲染或 GPU 兼容性测试通过。
