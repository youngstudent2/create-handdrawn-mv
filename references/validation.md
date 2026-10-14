# 项目检查脚本

从技能根目录运行命令，或把脚本替换成其绝对路径。Python 3；计划检查仅用标准库，图片检查依赖 Pillow，视频检查依赖 ffprobe，完整解码依赖 FFmpeg。

```bash
python scripts/check_project.py /path/to/project.json --plan-only
python scripts/check_project.py /path/to/project.json --contact-sheet /path/to/output/keyframes.jpg --report /path/to/output/assets.json
python scripts/check_project.py /path/to/project.json --video /path/to/output/final.mp4 --usage /path/to/output/usage.json --decode --report /path/to/output/final-check.json
```

所有素材路径相对 `project.json` 所在目录解析，也接受绝对路径；命令行输出文件路径相对当前工作目录解析。素材仅被读取；总览、报告只写到指定输出位置。JSON 模板是结构与分镜示例，不包含可直接出片的图片或音轨。

## 检查范围

- `--plan-only`：时长、连续时间线、画幅、帧率、镜头与姿势 ID、动作描述、最低关键帧数量、重复文件引用。无需素材文件存在。
- 默认素材检查：图片可读、真实 alpha、空图、同镜头画布尺寸一致、解码像素重复、轮廓贴边警告。`allow_edge_crop: true` 仅关闭该图贴边警告，不证明裁切合理。
- `--video`：视频流、输出尺寸、平均帧率、时长、容器可用帧数与要求的音轨是否存在。该流程要求正偶数宽高，适用于常见 H.264/yuv420p MP4。
- `--decode`：调用 FFmpeg 完整解码音视频，检查解码错误；必须同时提供 `--video`。
- `--usage`：将计划文件与渲染器实际记录比较。记录相对清单目录的完整素材路径，不只写容易歧义的文件名或 stem。
- `--contact-sheet`：生成已有图片的四列总览，不生成新素材。
- `--report`：另存与标准输出相同的 JSON。存在错误返回退出码 1；自动检查通过返回 0，仍可能有人工待查警告。

渲染器输出的 usage 格式：

```json
{
  "used_keyframes": ["assets/shot_01_A.png", "assets/shot_01_B.png"],
  "shown_frames": {"assets/shot_01_A.png": 24, "assets/shot_01_B.png": 27}
}
```

`shown_frames` 可省略；有条件时由渲染器在素材实际绘制时累计，不根据目录或计划倒推。计数必须是正整数，但本脚本不保证绘制后未被遮挡。不可为通过检查而编造记录。

脚本不识别换色、镜像、近似重复姿势，不判断手指/身份一致性，不判断音画同步或舞台表演。像素不同只证明图不同，不能证明姿势不同；音轨存在不证明有声、正确选曲或正确截取。自动检查后仍须看图和播放成片。

## 返修检查与文件完整性

额外记录每个修改切点前后连续帧的时间码，以及原画、编码后画面、播放/音频检查各自完成到哪一步。只检查截图不能写“已观看整片”。最终片尾须在文字原定出现后的多个时间点复查。

遇到 PNG 截断，重新读取原文件或从已保存工程恢复；保存时可先写临时文件、关闭并完整解码，再原子替换。不要开启 `LOAD_TRUNCATED_IMAGES` 来掩盖损坏，也不要仅通过读出尺寸就认定文件完整。修复后重新读取实际进入渲染器的路径。

旧工程本就使用纸底图片时，不为通过检查批量伪造透明图。保留获准的素材形式，在清单如实设置全局 `requires_alpha`，另逐张确认新建透明素材的 alpha；不能靠关闭检查掩盖本应透明的新素材问题。
