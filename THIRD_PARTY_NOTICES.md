# 第三方资料与来源署名

## 固定实验数据

- 数据记录作者：**Steffen Brundiers**，Leibniz University Hannover。
- 标题：*Datasets: Time-Resolved Performance and Stability of Different Gas Recombination Catalysts in PEM Water Electrolysis*。
- 发布日期：2026-04-01；固定 DOI：[10.5281/zenodo.19361280](https://doi.org/10.5281/zenodo.19361280)。
- 许可：[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)。
- 原始文件：`pem_water_electrolysis_degradation_data.zip`，199357168 字节。
- Zenodo 官方 MD5：`b161b3a2eb0d655266bd13618da386a7`。
- 本次计算的 SHA-256：`ef15233374ece3af33a3f876a80d8a7c38c965dff122b884c6ebd39f391952e4`。

2026-10-22 再次读取官方 API，确认许可、大小和 MD5 与本地原始包一致。检查记录见 [upstream_verification.json](provenance/upstream_verification.json)。官方元数据原始快照保存在 `01_raw/zenodo_19361280.json`；原始 ZIP 由复现入口按需获取。

## 上游数据说明与论文

`01_raw/readMe_dataset_documentation.txt` 是原始 ZIP 中五页 PDF 说明的文本转录，保留原作者的内容、联系信息及许可说明。它不是本项目的新文档，也不是期刊完整补充材料。转录有 PDF 断词和排版损失，原版请以固定 ZIP 内 PDF 为准。

该说明列出的研究作者为 Steffen Brundiers、Patrick Trinke、Simon Geiger、Victor-Alfonso Gracia-Medrano-Bravo、Marek Hubka、Jan Ilsemann、Boris Bensmann、Richard Hanke-Rauschenbach。相关论文：

Brundiers S, et al. *Time-resolved performance and stability of different gas recombination catalysts in PEM water electrolysis*. EES Catalysis, 2026. DOI: [10.1039/D6EY00106H](https://doi.org/10.1039/D6EY00106H)。

## 本项目做出的改动

本项目抽取非空稀释校正 GC 记录和操作段，将高低载阶段配对，建立尾窗终点及因果可用特征，进行回顾性时间切分、冻结预测、稀疏标签模拟、指数敏感性和图表分析。派生表、预测和解释属于本项目再分析，不能标成原作者发表的结果。

不前向填充稀疏 GC 值，不按相同读数删除真实观测。数据处理定义见 [数据字典](02_processed/数据字典.md)。本项目与上游作者不存在本包所声明的合作或背书关系。

