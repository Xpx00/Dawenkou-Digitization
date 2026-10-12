# 大汶口文物数字化 · 41件核验水密模型

[English](README.md) · [下载数据](https://github.com/Xpx00/Dawenkou-Digitization/releases/tag/v1.0.0) · [器物清单](metadata/objects.csv) · [新旧编号映射](metadata/id_mapping.csv)

本仓库公开41件人工核验的彩色水密模型，以及对应的重建输入：
**40件陶器、1件石纺轮、4,620张注册图片、4,620张前景mask、原始COLMAP相机与稀疏点云**。

它是PAR真实数字化应用的筛选成果集合，不是完整采集队列，也不是不可见底面的几何GT。

## 下载与使用

Git仓库保存说明、索引和校验脚本。完整数据放在同一仓库的
[v1.0.0 Release](https://github.com/Xpx00/Dawenkou-Digitization/releases/tag/v1.0.0)：

- `dawenkou41-models-v1.0.0.zip`：41个PLY、41个GLB与每件器物的元数据，约140 MiB。
- `dawenkou41-multiview-v1.0.0.zip`：图像、mask、COLMAP二进制、相机JSON与视图对应表，约601 MiB。

```bash
git clone https://github.com/Xpx00/Dawenkou-Digitization.git
cd Dawenkou-Digitization
python3 scripts/download.py --component all
python3 -m pip install -r requirements.txt
python3 scripts/verify_dataset.py
```

只需要模型时，将下载与核验命令中的`--component`设置为`models`。
只clone不会自动下载模型或图像；下载脚本核对压缩包及解压文件的SHA256。

## 整理原则

- 对象按原编号从小到大排序，重新连续编号为`DWK_0001`至`DWK_0041`。
  **新序号与旧实验序号不是同一编号体系**，对应关系见映射表。
  旧`DWK_0073`现在是`DWK_0022`；石器旧`DWK_0040`现在是`DWK_0013`。
- 每件器物统一放在`objects/<新ID>/`，同目录保存`model.ply`、`model.glb`、
  `metadata.json`、`images/`、`masks/`、`sparse/0/`、`cameras.json`与`views.csv`。
- 保留原视图表实际索引的mask，每图一份；4,620张逐字节相同的兼容副本已去除。
  原mask文件名仍为`frame_xxxxx.jpg.png`，对应表不歧义。
- 保留原COLMAP全部5个二进制文件；可由`points3D.bin`生成的稀疏PLY副本已去除。
- 系统文件、单件重复压缩包、旧大清单与工程日志不作为公开数据内容。
- 原图片、模型、选中mask、相机JSON和COLMAP二进制逐字节不变。
  只重排对象目录和索引，不改坐标、颜色、模型精度、图像分辨率或相机解。

## 评价与复现边界

PLY/GLB与相机在原SfM坐标系中；物体竖直方向以`up_axis`为准。
未标定共同物理尺度，单位不是毫米。隐藏底面的形状和颜色是补全与外推。
闭合网格不等于底部真实精度、语义开口、壁厚或打印适用性均已验证。

41件模型中，33件来自前景包络约束Poisson（HVE），8件来自标准Poisson（T0）。
这不是两个方法的成功率比较，也不是100%自动产出的宣称。

本包能用于模型检查、展示，以及从给定图像、mask和标定重新构建对象。
VGGT-Ω缓存、高斯检查点、补全前TSDF和完整PAR训练代码没有包含在本数据仓库中，
因此不能仅凭此包逐位复现历史最终模型。具体见[复现说明](docs/REPRODUCTION.md)。

## 许可

用户指定采用**[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)**：
署名、注明修改、非商业复用。正式条款见[LICENSE](LICENSE)。
引用发布账户`Xpx00`、数据集名称、版本与仓库链接；不虚构发布机构或DOI。
